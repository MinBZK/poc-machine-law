<script lang="ts">
  import yaml from 'yaml';
  import { untrack } from 'svelte';
  import {
    MarkerType,
    SvelteFlow,
    Controls,
    Background,
    BackgroundVariant,
    MiniMap,
    type Node,
    type Edge,
    Position,
  } from '@xyflow/svelte';
  import HierarchyNode from './HierarchyNode.svelte';
  import { exportViewportToPng, exportViewportToSvg } from '$lib/exportUtils';

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  // Layout configuration constants
  const LAYOUT_CONFIG = {
    NODE_WIDTH: 280,
    NODE_HEIGHT: 100,
    X_SPACING: 450,
    Y_SPACING: 120,
    ORPHAN_X_OFFSET_COLUMNS: 2,
    GRID_NODES_PER_COLUMN: 10,
    MAX_SERVICE_COLORS: 7,
  } as const;

  type Law = {
    uuid: string;
    name: string;
    service: string;
    valid_from: string;
    law_type?: string;
    properties: {
      sources?: { name: string }[];
      input?: { name: string; service_reference?: { service: string; law: string; field: string } }[];
      output?: { name: string }[];
    };
  };

  // Check if demo mode is enabled via URL parameter
  const isDemoMode = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('demo') === 'true';

  let filePaths: string[] = [];
  let nodes = $state<Node[]>([]);
  let edges = $state<Edge[]>([]);

  const nodeTypes: any = {
    hierarchy: HierarchyNode,
  };

  let flowInstance: any = $state(null);
  let isExporting = $state(false);

  function oninit(instance: any) {
    flowInstance = instance;
  }

  async function exportToPng() {
    if (nodes.length === 0) {
      alert('Geen wetten om te exporteren. Selecteer eerst enkele wetten.');
      return;
    }

    isExporting = true;
    try {
      await exportViewportToPng(nodes, 'zorgtoeslagwet-hierarchy');
    } catch (error) {
      console.error('Error exporting to PNG:', error);
      alert('Fout bij exporteren naar PNG. Zie console voor details.');
    } finally {
      isExporting = false;
    }
  }

  async function exportToSvg() {
    if (nodes.length === 0) {
      alert('Geen wetten om te exporteren. Selecteer eerst enkele wetten.');
      return;
    }

    isExporting = true;
    try {
      await exportViewportToSvg(nodes, 'zorgtoeslagwet-hierarchy');
    } catch (error) {
      console.error('Error exporting to SVG:', error);
      alert('Fout bij exporteren naar SVG. Zie console voor details.');
    } finally {
      isExporting = false;
    }
  }


  // Map service names to color indices (0-6)
  const serviceToColorIndex = new Map<string, number>();
  let nextColorIndex = 0;

  function getServiceColorIndex(service: string): number {
    if (!serviceToColorIndex.has(service)) {
      serviceToColorIndex.set(service, nextColorIndex % LAYOUT_CONFIG.MAX_SERVICE_COLORS);
      nextColorIndex++;
    }
    return serviceToColorIndex.get(service)!;
  }

  let laws = $state<Law[]>([]);
  let selectedLaws = $state<string[]>([]);
  let lawPathMap = new Map<string, string>(); // Maps UUID to file path

  // Function to rebuild nodes and edges based on selected laws
  function rebuildNodesAndEdges() {
    if (laws.length === 0) return;

    const ns: Node[] = [];
    const es: Edge[] = [];

    // Create nodes ONLY for selected laws
    const selectedSet = new Set(selectedLaws);

    for (const law of laws) {
      // Skip laws that are not selected
      if (!selectedSet.has(law.uuid)) continue;

      const layer = determineLawLayer(law.law_type || 'FORMELE_WET');
      const colorIndex = getServiceColorIndex(law.service);

      ns.push({
        id: law.uuid,
        type: 'hierarchy',
        data: {
          label: law.name,
          layer: layer,
          service: law.service,
        },
        position: { x: 0, y: 0 }, // Will be set by layoutTree
        width: LAYOUT_CONFIG.NODE_WIDTH,
        height: LAYOUT_CONFIG.NODE_HEIGHT,
        class: `hierarchy-node service-${colorIndex}`,
        sourcePosition: Position.Left,
        targetPosition: Position.Right,
      });
    }

    // Build index for O(1) lookup: service -> laws (performance optimization)
    const lawsByService = new Map<string, Law[]>();
    for (const law of laws) {
      if (!lawsByService.has(law.service)) {
        lawsByService.set(law.service, []);
      }
      lawsByService.get(law.service)!.push(law);
    }

    // Create edges based on service_references (only for selected laws)
    // Now O(n*m) instead of O(n²) where m = avg laws per service
    for (const law of laws) {
      if (!selectedSet.has(law.uuid)) continue;

      for (const input of law.properties.input || []) {
        const ref = input.service_reference;
        if (!ref) continue;

        // O(m) lookup instead of O(n) - much faster with many laws!
        const candidateLaws = lawsByService.get(ref.service) || [];
        for (const sourceLaw of candidateLaws) {
          if (ref.law) {
            const sourcePath = lawPathMap.get(sourceLaw.uuid) || '';
            if (!sourcePath.includes(ref.law)) continue;
          }

          // Check if this law outputs the referenced field
          const hasOutput = sourceLaw.properties.output?.some(o => o.name === ref.field);
          if (!hasOutput) continue;

          // Create edge from source law to current law
          es.push({
            id: `${sourceLaw.uuid}-${law.uuid}-${ref.field}`,
            source: sourceLaw.uuid,
            target: law.uuid,
            label: ref.field,
            type: 'bezier',
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 40,
            },
            animated: true,
          });
          break; // Only create one edge per input
        }
      }
    }

    nodes = ns;
    edges = es;

    // Auto-layout the tree
    layoutTree();

    // Fit view after layout
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (flowInstance) {
          flowInstance.fitView({ padding: 0.2, duration: 800 });
        }
      });
    });
  }

  // Determine the layer of a law based on its law_type from YAML
  function determineLawLayer(lawType: string): string {
    // Map law_type values to display labels
    // Currently only FORMELE_WET exists in schema, but this is extensible
    const typeMap: Record<string, string> = {
      'FORMELE_WET': 'wet',
      'AMVB': 'amvb',
      'REGELING': 'regeling',
      'BELEIDSREGEL': 'beleidsregel',
      'WERKINSTRUCTIE': 'werkinstructie',
    };

    return typeMap[lawType] || lawType.toLowerCase();
  }

  // Build a hierarchy map: parent UUID -> child UUIDs
  function buildHierarchy(laws: Law[]): Map<string, string[]> {
    const hierarchy = new Map<string, string[]>();

    // For each law, find its children via service_references
    for (const law of laws) {
      const children: string[] = [];

      // Check if any other laws reference this law
      for (const otherLaw of laws) {
        if (otherLaw.uuid === law.uuid) continue;

        for (const input of otherLaw.properties.input || []) {
          const ref = input.service_reference;
          if (ref && ref.service === law.service) {
            // Check if the referenced law matches this law's name/path
            const refLawPath = lawPathMap.get(law.uuid) || '';
            if (ref.law && refLawPath.includes(ref.law)) {
              if (!children.includes(otherLaw.uuid)) {
                children.push(otherLaw.uuid);
              }
            }
          }
        }
      }

      if (children.length > 0) {
        hierarchy.set(law.uuid, children);
      }
    }

    return hierarchy;
  }

  (async () => {
    try {
      // Fetch the available laws from the backend
      const response = await fetch('/laws/list');
      filePaths = await response.json();

      let allLaws = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content - construct URL properly
          const lawUrl = `/analysis/hierarchy/law/${filePath}`;
          const response = await fetch(lawUrl);
          if (!response.ok) {
            throw new Error(`Failed to fetch law ${filePath}: ${response.statusText}`);
          }
          const fileContent = await response.text();

          // Parse the YAML content
          const law = yaml.parse(fileContent) as Law;

          // Store the file path for this law
          lawPathMap.set(law.uuid, filePath);

          return law;
        }),
      );

      // Filter to keep only the latest version of each law (by service and name)
      const lawMap = new Map<string, Law>();
      for (const law of allLaws) {
        const key = `${law.service}:${law.name}`;
        const existing = lawMap.get(key);

        if (!existing || law.valid_from > existing.valid_from) {
          lawMap.set(key, law);
        }
      }

      laws = Array.from(lawMap.values());

      // Initialize selected laws: ONLY Zorgtoeslag and its direct dependencies
      // Find the Zorgtoeslag law
      const zorgtoeslagwet = laws.find(law =>
        law.name.toLowerCase().includes('zorgtoeslag')
      );

      if (zorgtoeslagwet) {
        // Start with Zorgtoeslagwet
        const selectedSet = new Set<string>([zorgtoeslagwet.uuid]);

        // Add ALL laws that are in the zorgtoeslagwet directory tree
        for (const law of laws) {
          const filePath = lawPathMap.get(law.uuid) || '';
          if (filePath.includes('zorgtoeslagwet/')) {
            selectedSet.add(law.uuid);
          }
        }

        // Build edges first
        const lawEdges: Array<{source: string, target: string}> = [];

        // Step 1: Add service_reference edges (normal dependencies)
        for (const law of laws) {
          for (const input of law.properties.input || []) {
            const ref = input.service_reference;
            if (!ref) continue;

            for (const sourceLaw of laws) {
              if (sourceLaw.service !== ref.service) continue;

              if (ref.law) {
                const sourcePath = lawPathMap.get(sourceLaw.uuid) || '';
                if (!sourcePath.includes(ref.law)) continue;
              }

              const hasOutput = sourceLaw.properties.output?.some(o => o.name === ref.field);
              if (!hasOutput) continue;

              lawEdges.push({ source: sourceLaw.uuid, target: law.uuid });
              break;
            }
          }
        }

        // Step 2: Add hierarchy edges for zorgtoeslagwet (hoofdwet -> regelingen/beleidsregels)
        const zorgtoeslagHoofdwet = laws.find(law => {
          const path = lawPathMap.get(law.uuid) || '';
          return path.startsWith('zorgtoeslagwet/TOESLAGEN-') && !path.includes('/regelingen/') && !path.includes('/beleidsregels/');
        });

        if (zorgtoeslagHoofdwet) {
          for (const law of laws) {
            const path = lawPathMap.get(law.uuid) || '';
            // If this is a regeling or beleidsregel under zorgtoeslagwet, add hierarchy edge
            if ((path.includes('zorgtoeslagwet/regelingen/') || path.includes('zorgtoeslagwet/beleidsregels/'))
                && law.uuid !== zorgtoeslagHoofdwet.uuid) {
              // Edge goes FROM hoofdwet TO regeling/beleidsregel (delegation)
              lawEdges.push({ source: zorgtoeslagHoofdwet.uuid, target: law.uuid });
            }
          }
        }

        // Traverse ONLY edges where Zorgtoeslagwet is the TARGET (it depends on source)
        const toProcess = [zorgtoeslagwet.uuid];
        const processed = new Set<string>();

        while (toProcess.length > 0) {
          const currentUuid = toProcess.pop()!;
          if (processed.has(currentUuid)) continue;
          processed.add(currentUuid);

          // Find edges where current node is TARGET
          for (const edge of lawEdges) {
            if (edge.target === currentUuid && !selectedSet.has(edge.source)) {
              selectedSet.add(edge.source);
              toProcess.push(edge.source);
            }
          }
        }

        selectedLaws = Array.from(selectedSet);
      } else {
        // Fallback: show all laws
        selectedLaws = laws.map((law) => law.uuid);
      }

      // Build nodes and edges based on selected laws
      rebuildNodesAndEdges();
    } catch (error) {
      console.error('Error loading laws:', error);
    }
  })();

  // Layout algorithm: Zorgtoeslagwet on LEFT, dependencies to the RIGHT
  function layoutTree() {
    if (nodes.length === 0) {
      return;
    }

    const visibleNodeIds = new Set(nodes.filter(n => !n.hidden).map(n => n.id));
    const visibleEdges = edges.filter(e => !e.hidden);


    // Find Zorgtoeslag as the starting point (leftmost)
    const zorgtoeslagwet = nodes.find(n =>
      !n.hidden && n.data.label.toLowerCase().includes('zorgtoeslag')
    );

    if (!zorgtoeslagwet) {
      simpleGridLayout();
      return;
    }


    // Calculate depth by traversing dependencies (edges point FROM dependency TO dependent)
    // Edge: source -> target means "source provides data to target"
    // So target depends on source
    // We want to traverse: target -> its sources (dependencies)
    const depths = new Map<string, number>();
    const processing = new Set<string>(); // Track nodes currently being processed to detect cycles
    const nodesWithCycles = new Set<string>(); // Track which nodes have circular dependencies

    function calculateDepth(nodeId: string, currentDepth: number) {
      // Detect cycles: if we're already processing this node, we have a circular dependency
      if (processing.has(nodeId)) {
        const nodeName = nodes.find(n => n.id === nodeId)?.data.label;
        console.warn(`Circular dependency detected at node: ${nodeName}`);
        nodesWithCycles.add(nodeId);
        // Still set depth to position the node, even if it's in a cycle
        if (!depths.has(nodeId)) {
          depths.set(nodeId, currentDepth);
        }
        return;
      }

      // Update depth if this is deeper than previously found
      const currentNodeDepth = depths.get(nodeId) ?? -1;
      if (currentDepth <= currentNodeDepth) {
        return; // Already processed via a longer path
      }

      depths.set(nodeId, currentDepth);
      processing.add(nodeId);

      // Find all edges where this node is the TARGET (it depends on sources)
      for (const edge of edges) {
        if (edge.hidden) continue;
        if (edge.target === nodeId && visibleNodeIds.has(edge.source)) {
          // This node depends on edge.source, so source should be deeper (more to the right)
          calculateDepth(edge.source, currentDepth + 1);
        }
      }

      processing.delete(nodeId);
    }

    // Start from Zorgtoeslagwet at depth 0
    calculateDepth(zorgtoeslagwet.id, 0);

    // Find orphaned nodes (nodes without a depth assignment)
    const orphanedNodes: string[] = [];
    for (const node of nodes) {
      if (!node.hidden && !depths.has(node.id)) {
        orphanedNodes.push(node.id);
      }
    }

    // Group nodes by depth
    const nodesByDepth = new Map<number, string[]>();
    for (const [nodeId, depth] of depths.entries()) {
      if (!nodesByDepth.has(depth)) nodesByDepth.set(depth, []);
      nodesByDepth.get(depth)!.push(nodeId);
    }

    // Position nodes
    const xSpacing = LAYOUT_CONFIG.X_SPACING;
    const ySpacing = LAYOUT_CONFIG.Y_SPACING;
    const maxDepth = depths.size > 0 ? Math.max(...depths.values()) : 0;


    for (let depth = 0; depth <= maxDepth; depth++) {
      const nodesAtDepth = nodesByDepth.get(depth) || [];
      const x = depth * xSpacing;

      // Calculate total height needed
      const totalHeight = nodesAtDepth.length * ySpacing;
      let y = -totalHeight / 2; // Center vertically


      for (const nodeId of nodesAtDepth) {
        const nodeIndex = nodes.findIndex(n => n.id === nodeId);
        if (nodeIndex !== -1) {
          const nodeName = nodes[nodeIndex].data.label;
          nodes[nodeIndex] = {
            ...nodes[nodeIndex],
            position: { x, y },
            data: {
              ...nodes[nodeIndex].data,
              hasCircularDependency: nodesWithCycles.has(nodeId),
            },
          };
          y += ySpacing;
        }
      }
    }

    // Position orphaned nodes in a separate column to the far right
    if (orphanedNodes.length > 0) {
      const orphanX = (maxDepth + LAYOUT_CONFIG.ORPHAN_X_OFFSET_COLUMNS) * xSpacing;
      const orphanTotalHeight = orphanedNodes.length * ySpacing;
      let orphanY = -orphanTotalHeight / 2;


      for (const nodeId of orphanedNodes) {
        const nodeIndex = nodes.findIndex(n => n.id === nodeId);
        if (nodeIndex !== -1) {
          nodes[nodeIndex] = {
            ...nodes[nodeIndex],
            position: { x: orphanX, y: orphanY },
            data: {
              ...nodes[nodeIndex].data,
              hasCircularDependency: nodesWithCycles.has(nodeId),
            },
          };
          orphanY += ySpacing;
        }
      }
    }

    // Safety check: if most nodes are orphaned, use grid layout instead
    const positionedNodesCount = depths.size;
    if (orphanedNodes.length > positionedNodesCount && orphanedNodes.length > 3) {
      simpleGridLayout();
      return;
    }

    nodes = [...nodes]; // Trigger reactivity
  }

  // Simple grid layout fallback for when tree structure is not available
  function simpleGridLayout(nodesWithCycles: Set<string> = new Set()) {
    const visibleNodes = nodes.filter(n => !n.hidden);
    const xSpacing = LAYOUT_CONFIG.X_SPACING;
    const ySpacing = LAYOUT_CONFIG.Y_SPACING;
    const nodesPerColumn = LAYOUT_CONFIG.GRID_NODES_PER_COLUMN;


    let nodeIndex = 0;
    for (const node of visibleNodes) {
      const col = Math.floor(nodeIndex / nodesPerColumn);
      const row = nodeIndex % nodesPerColumn;

      const x = col * xSpacing;
      const y = (row - nodesPerColumn / 2) * ySpacing;

      const idx = nodes.findIndex(n => n.id === node.id);
      if (idx !== -1) {
        nodes[idx] = {
          ...nodes[idx],
          position: { x, y },
          data: {
            ...nodes[idx].data,
            hasCircularDependency: nodesWithCycles.has(node.id),
          },
        };
      }
      nodeIndex++;
    }

    nodes = [...nodes]; // Trigger reactivity
  }

  // Handle changes to selectedLaws only
  $effect(() => {
    // Only track selectedLaws changes
    const lawsCount = selectedLaws.length;

    untrack(() => {
      // Don't run until laws are loaded
      if (laws.length === 0) return;

      // Rebuild nodes and edges based on new selection
      rebuildNodesAndEdges();
    });
  });
</script>

<svelte:head>
  <title>Hierarchy — RegelRecht</title>
</svelte:head>

<div class="float-right h-screen w-80 overflow-y-auto px-6 pb-4 text-sm">
  <div class="sticky top-0 bg-white pt-6 pb-2">
    <h1 class="mb-3 text-base font-semibold">Wetgevings-hiërarchie</h1>
    <p class="mb-4 text-xs text-gray-600">
      Visualisatie van de gelaagde structuur: van formele wetten tot uitvoeringsbeleid.
    </p>

    <div class="flex flex-col gap-2 mb-4">
      <button
        type="button"
        onclick={layoutTree}
        class="cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-3 py-1.5 text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
        >Her-positioneer</button
      >
      <button
        type="button"
        onclick={() => {
          selectedLaws = laws.map((law) => law.uuid);
        }}
        class="cursor-pointer rounded-md border border-gray-600 bg-gray-600 px-3 py-1.5 text-white transition duration-200 hover:border-gray-700 hover:bg-gray-700"
        >Selecteer alles</button
      >
      <div class="flex gap-2">
        <button
          type="button"
          onclick={exportToPng}
          disabled={isExporting}
          class="flex-1 cursor-pointer rounded-md border border-emerald-600 bg-emerald-600 px-3 py-1.5 text-white transition duration-200 hover:border-emerald-700 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >{isExporting ? 'Exporteren...' : 'PNG'}</button
        >
        <button
          type="button"
          onclick={exportToSvg}
          disabled={isExporting}
          class="flex-1 cursor-pointer rounded-md border border-emerald-600 bg-emerald-600 px-3 py-1.5 text-white transition duration-200 hover:border-emerald-700 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >{isExporting ? 'Exporteren...' : 'SVG'}</button
        >
      </div>
    </div>
  </div>

  {#each Object.entries(laws.reduce((acc, law) => {
        if (!acc[law.service]) acc[law.service] = [];
        acc[law.service].push(law);
        return acc;
      }, {} as Record<string, Law[]>)) as [service, serviceLaws]}
    <h2
      class="service-{getServiceColorIndex(
        service,
      )} mt-4 mb-2 inline-block rounded-md px-2 py-1 text-sm font-semibold first:mt-0"
    >
      {service}
    </h2>
    {#each serviceLaws as law}
      <div class="mb-1.5">
        <label class="group inline-flex items-start">
          <input
            bind:group={selectedLaws}
            class="form-checkbox mt-0.5 mr-1.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            type="checkbox"
            value={law.uuid}
          />
          <span class="text-xs"
            >{law.name}
            <button
              type="button"
              onclick={() => {
                selectedLaws = [law.uuid];
              }}
              class="invisible cursor-pointer font-semibold text-blue-700 group-hover:visible hover:text-blue-800"
              >alleen</button
            ></span
          >
        </label>
      </div>
    {/each}
  {/each}
</div>

<div class="mr-80 h-screen">
  <SvelteFlow
    bind:nodes
    bind:edges
    {nodeTypes}
    {oninit}
    fitView
    nodesConnectable={false}
    proOptions={{
      hideAttribution: true,
    }}
    minZoom={0.1}
  >
    <Controls showLock={false} />
    <Background variant={BackgroundVariant.Dots} />
    <MiniMap
      zoomable
      pannable
      nodeColor={(n) => (!n.hidden ? '#ccc' : 'transparent')}
    />
  </SvelteFlow>
</div>

<style lang="postcss">
  @reference "tailwindcss/theme";

  :global(.hierarchy-node) {
    @apply rounded-md border-2 p-2;
  }

  /* Service colors */
  :global(.service-0.hierarchy-node) {
    @apply border-blue-800 bg-blue-50;
  }

  :global(.service-1.hierarchy-node) {
    @apply border-pink-800 bg-pink-50;
  }

  :global(.service-2.hierarchy-node) {
    @apply border-emerald-800 bg-emerald-50;
  }

  :global(.service-3.hierarchy-node) {
    @apply border-amber-800 bg-amber-50;
  }

  :global(.service-4.hierarchy-node) {
    @apply border-purple-800 bg-purple-50;
  }

  :global(.service-5.hierarchy-node) {
    @apply border-yellow-800 bg-yellow-50;
  }

  :global(.service-6.hierarchy-node) {
    @apply border-slate-800 bg-slate-50;
  }

  /* Sidebar service colors */
  .service-0 {
    @apply bg-blue-100 text-blue-800;
  }

  .service-1 {
    @apply bg-pink-100 text-pink-800;
  }

  .service-2 {
    @apply bg-emerald-100 text-emerald-800;
  }

  .service-3 {
    @apply bg-amber-100 text-amber-800;
  }

  .service-4 {
    @apply bg-purple-100 text-purple-800;
  }

  .service-5 {
    @apply bg-yellow-100 text-yellow-800;
  }

  .service-6 {
    @apply bg-slate-100 text-slate-800;
  }

  :global(.svelte-flow) {
    --xy-edge-stroke: #8b5cf6;
    --xy-edge-stroke-selected: #8b5cf6;
  }

  :global(.svelte-flow__arrowhead polyline) {
    @apply !fill-purple-500 !stroke-purple-500;
  }

  :global(.svelte-flow__edge.selected) {
    --xy-edge-stroke-width-default: 2.5;
  }

  :global(.svelte-flow__edge.animated) {
    animation: dashdraw 0.5s linear infinite;
    stroke-dasharray: 5;
  }

  @keyframes dashdraw {
    to {
      stroke-dashoffset: -10;
    }
  }
</style>
