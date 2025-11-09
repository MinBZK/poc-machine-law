<script lang="ts">
  import yaml from 'yaml';
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
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
  import { exportViewportToPng, exportViewportToPdf } from '$lib/exportUtils';

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  type Law = {
    uuid: string;
    name: string;
    service: string;
    valid_from: string;
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

  function onInit(instance: any) {
    flowInstance = instance;
    console.log('SvelteFlow initialized');
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

  async function exportToPdf() {
    if (nodes.length === 0) {
      alert('Geen wetten om te exporteren. Selecteer eerst enkele wetten.');
      return;
    }

    isExporting = true;
    try {
      await exportViewportToPdf(nodes, 'zorgtoeslagwet-hierarchy');
    } catch (error) {
      console.error('Error exporting to PDF:', error);
      alert('Fout bij exporteren naar PDF. Zie console voor details.');
    } finally {
      isExporting = false;
    }
  }

  // Monitor when nodes are measured
  $effect(() => {
    const measuredNodes = nodes.filter(n => n.measured);
    if (measuredNodes.length > 0) {
      console.log(`Measured nodes: ${measuredNodes.length}/${nodes.length}`);
    }
  });

  // Monitor edges array
  $effect(() => {
    console.log('Edges state changed:', edges.length, 'edges');
    if (edges.length > 0) {
      console.log('First edge in state:', edges[0]);
    }
  });

  // Map service names to color indices (0-6)
  const serviceToColorIndex = new Map<string, number>();
  let nextColorIndex = 0;

  function getServiceColorIndex(service: string): number {
    if (!serviceToColorIndex.has(service)) {
      serviceToColorIndex.set(service, nextColorIndex % 7);
      nextColorIndex++;
    }
    return serviceToColorIndex.get(service)!;
  }

  let laws = $state<Law[]>([]);
  let selectedLaws = $state<string[]>([]);
  let lawPathMap = new Map<string, string>(); // Maps UUID to file path

  // Determine the layer of a law based on its file path
  function determineLawLayer(filePath: string): string {
    const lowerPath = filePath.toLowerCase();

    if (lowerPath.includes('/regelingen/') || lowerPath.includes('/regeling_')) {
      return 'regeling';
    } else if (lowerPath.includes('/beleidsregels/') || lowerPath.includes('/beleidsregel_')) {
      return 'beleidsregel';
    } else if (lowerPath.includes('/amvb/')) {
      return 'amvb';
    } else if (lowerPath.includes('/werkinstructies/') || lowerPath.includes('/werkinstructie_')) {
      return 'werkinstructie';
    } else {
      // Default to "wet" for main law files
      return 'wet';
    }
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

      const ns: Node[] = [];
      const es: Edge[] = [];

      let allLaws = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content
          // @ts-expect-error ts(2345)
          const fileContent = await fetch(resolve(`/law/${filePath}`)).then((response) =>
            response.text(),
          );

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
        console.log('Selected laws:', selectedLaws.length, 'starting from Zorgtoeslag (including all zorgtoeslagwet/* files)');

        // Group by layer to see what we have
        const selectedByLayer = new Map<string, string[]>();
        for (const uuid of selectedSet) {
          const law = laws.find(l => l.uuid === uuid);
          if (!law) continue;
          const filePath = lawPathMap.get(uuid) || '';
          const layer = determineLawLayer(filePath);
          if (!selectedByLayer.has(layer)) selectedByLayer.set(layer, []);
          selectedByLayer.get(layer)!.push(law.name);
        }

        console.log('Selected by layer:');
        for (const [layer, names] of selectedByLayer.entries()) {
          console.log(`  ${layer}: ${names.length}`, names);
        }
      } else {
        // Fallback: show all laws
        selectedLaws = laws.map((law) => law.uuid);
      }

      // Create nodes ONLY for selected laws
      const selectedSet = new Set(selectedLaws);

      for (const law of laws) {
        // Skip laws that are not selected
        if (!selectedSet.has(law.uuid)) continue;

        const filePath = lawPathMap.get(law.uuid) || '';
        const layer = determineLawLayer(filePath);
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
          width: 280,
          height: 100,
          class: `hierarchy-node service-${colorIndex}`,
          sourcePosition: Position.Left,
          targetPosition: Position.Right,
        });
      }

      // Create edges based on service_references (only for selected laws)
      for (const law of laws) {
        // Skip if target law is not selected
        if (!selectedSet.has(law.uuid)) continue;

        for (const input of law.properties.input || []) {
          const ref = input.service_reference;
          if (!ref) continue;

          // Find the law that provides this reference
          for (const sourceLaw of laws) {
            // Skip if source law is not selected
            if (!selectedSet.has(sourceLaw.uuid)) continue;
            if (sourceLaw.service !== ref.service) continue;

            // If ref.law is specified, check if the source path matches
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

      console.log('Created', ns.length, 'nodes and', es.length, 'edges');
      console.log('Node names:', ns.map(n => n.data.label));
      console.log('Sample edges:', es.slice(0, 3));
      console.log('Edge 0:', es[0]);

      // Verify edges connect to actual nodes
      const nodeIds = new Set(ns.map(n => n.id));
      const validEdges = es.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
      const invalidEdges = es.filter(e => !nodeIds.has(e.source) || !nodeIds.has(e.target));
      console.log(`Valid edges: ${validEdges.length}/${es.length}, Invalid: ${invalidEdges.length}`);
      if (invalidEdges.length > 0) {
        console.log('Sample invalid edge:', invalidEdges[0]);
      }

      console.log('Selected laws:', selectedLaws.length);

      // Auto-layout the tree
      layoutTree();

      console.log('After layout, visible nodes:', nodes.filter(n => !n.hidden).length);
      console.log('After layout, first 5 node positions:', nodes.slice(0, 5).map(n => ({
        label: n.data.label,
        pos: n.position,
        hidden: n.hidden
      })));

      // Fit view after a short delay to ensure layout is complete
      setTimeout(() => {
        if (flowInstance) {
          flowInstance.fitView({ padding: 0.2, duration: 800 });
        }

        // Debug: Check edge rendering
        setTimeout(() => {
          const edgeEls = document.querySelectorAll('.svelte-flow__edge');
          console.log(`DOM edges found: ${edgeEls.length}`);
          if (edgeEls.length > 0) {
            const firstEdge = edgeEls[0];
            const path = firstEdge.querySelector('path');
            if (path) {
              const styles = window.getComputedStyle(path);
              console.log('First edge path styles:', {
                stroke: styles.stroke,
                strokeWidth: styles.strokeWidth,
                display: styles.display,
                visibility: styles.visibility,
                opacity: styles.opacity,
                d: path.getAttribute('d')?.substring(0, 50)
              });
            }
          }
        }, 500);
      }, 200);
    } catch (error) {
      console.error('Error loading laws:', error);
    }
  })();

  // Layout algorithm: Zorgtoeslagwet on LEFT, dependencies to the RIGHT
  function layoutTree() {
    if (nodes.length === 0) {
      console.log('layoutTree: no nodes');
      return;
    }
    console.log('layoutTree: processing', nodes.length, 'nodes and', edges.length, 'edges');

    const visibleNodeIds = new Set(nodes.filter(n => !n.hidden).map(n => n.id));
    const visibleEdges = edges.filter(e => !e.hidden);

    console.log('Visible nodes:', visibleNodeIds.size, 'Visible edges:', visibleEdges.length);

    // Find Zorgtoeslag as the starting point (leftmost)
    const zorgtoeslagwet = nodes.find(n =>
      !n.hidden && n.data.label.toLowerCase().includes('zorgtoeslag')
    );

    if (!zorgtoeslagwet) {
      console.log('Zorgtoeslagwet not found - using simple grid layout');
      simpleGridLayout();
      return;
    }

    console.log('Starting from:', zorgtoeslagwet.data.label);

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

    // Log circular dependencies found
    if (nodesWithCycles.size > 0) {
      console.log('Nodes with circular dependencies:', Array.from(nodesWithCycles).map(id =>
        nodes.find(n => n.id === id)?.data.label
      ));
    }

    console.log('Depths calculated for', depths.size, 'nodes');
    console.log('Depth breakdown:', Array.from(depths.entries()).map(([id, depth]) => ({
      depth,
      name: nodes.find(n => n.id === id)?.data.label
    })));

    // Find orphaned nodes (nodes without a depth assignment)
    const orphanedNodes: string[] = [];
    for (const node of nodes) {
      if (!node.hidden && !depths.has(node.id)) {
        orphanedNodes.push(node.id);
      }
    }

    if (orphanedNodes.length > 0) {
      console.log('Found', orphanedNodes.length, 'orphaned nodes (not reachable from Zorgtoeslagwet):');
      console.log(orphanedNodes.map(id => nodes.find(n => n.id === id)?.data.label));
    }

    // Group nodes by depth
    const nodesByDepth = new Map<number, string[]>();
    for (const [nodeId, depth] of depths.entries()) {
      if (!nodesByDepth.has(depth)) nodesByDepth.set(depth, []);
      nodesByDepth.get(depth)!.push(nodeId);
    }

    // Position nodes
    const xSpacing = 450;
    const ySpacing = 120;
    const maxDepth = depths.size > 0 ? Math.max(...depths.values()) : 0;

    console.log('Max depth:', maxDepth);

    for (let depth = 0; depth <= maxDepth; depth++) {
      const nodesAtDepth = nodesByDepth.get(depth) || [];
      const x = depth * xSpacing;

      // Calculate total height needed
      const totalHeight = nodesAtDepth.length * ySpacing;
      let y = -totalHeight / 2; // Center vertically

      console.log(`Depth ${depth}: ${nodesAtDepth.length} nodes at x=${x}`);

      for (const nodeId of nodesAtDepth) {
        const nodeIndex = nodes.findIndex(n => n.id === nodeId);
        if (nodeIndex !== -1) {
          const nodeName = nodes[nodeIndex].data.label;
          console.log(`Positioning ${nodeName} at depth ${depth}: (${x}, ${y})`);
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
      const orphanX = (maxDepth + 2) * xSpacing; // Place 2 columns to the right of the deepest node
      const orphanTotalHeight = orphanedNodes.length * ySpacing;
      let orphanY = -orphanTotalHeight / 2;

      console.log(`Positioning ${orphanedNodes.length} orphaned nodes at x=${orphanX}`);

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
      console.log('Too many orphaned nodes - falling back to grid layout');
      simpleGridLayout();
      return;
    }

    nodes = [...nodes]; // Trigger reactivity
  }

  // Simple grid layout fallback for when tree structure is not available
  function simpleGridLayout(nodesWithCycles: Set<string> = new Set()) {
    const visibleNodes = nodes.filter(n => !n.hidden);
    const xSpacing = 450;
    const ySpacing = 120;
    const nodesPerColumn = 10;

    console.log('Using simple grid layout for', visibleNodes.length, 'nodes');

    let nodeIndex = 0;
    for (const node of visibleNodes) {
      const col = Math.floor(nodeIndex / nodesPerColumn);
      const row = nodeIndex % nodesPerColumn;

      const x = col * xSpacing;
      const y = (row - nodesPerColumn / 2) * ySpacing;

      const idx = nodes.findIndex(n => n.id === node.id);
      if (idx !== -1) {
        console.log(`Grid positioning node ${node.data.label} at (${x}, ${y})`);
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

    console.log('Grid layout complete, sample positions:', nodes.slice(0, 3).map(n => ({ label: n.data.label, pos: n.position })));
    nodes = [...nodes]; // Trigger reactivity
  }

  // Handle changes to selectedLaws only
  $effect(() => {
    // Only track selectedLaws changes
    const lawsCount = selectedLaws.length;

    untrack(() => {
      console.log('$effect triggered, selectedLaws:', lawsCount, 'nodes:', nodes.length);

      if (nodes.length === 0) return; // Don't run until nodes are loaded

      // Show only selected laws (no expansion)
      const selected = new Set(selectedLaws);

      nodes = nodes.map((node) => ({
        ...node,
        hidden: !selected.has(node.id),
      }));

      edges = edges.map((edge) => ({
        ...edge,
        hidden: !selected.has(edge.source) || !selected.has(edge.target),
      }));

      // Re-layout when selection changes
      layoutTree();
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
          >{isExporting ? 'PNG' : 'PNG'}</button
        >
        <button
          type="button"
          onclick={exportToPdf}
          disabled={isExporting}
          class="flex-1 cursor-pointer rounded-md border border-emerald-600 bg-emerald-600 px-3 py-1.5 text-white transition duration-200 hover:border-emerald-700 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >{isExporting ? 'PDF' : 'PDF'}</button
        >
      </div>
    </div>

    <div class="mb-4 border-t pt-3">
      <h2 class="text-sm font-semibold mb-2">Lagen</h2>
      <div class="space-y-1 text-xs">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-blue-600"></div>
          <span>Wet (formele wet)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-indigo-500"></div>
          <span>AMvB (algemene maatregel van bestuur)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-purple-500"></div>
          <span>Regeling (ministeriële regeling)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-pink-500"></div>
          <span>Beleidsregel</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-rose-400"></div>
          <span>Werkinstructie</span>
        </div>
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
    {onInit}
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
