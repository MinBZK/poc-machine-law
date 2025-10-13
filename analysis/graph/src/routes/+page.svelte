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
  import LawNode from './LawNode.svelte';

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  type Law = {
    uuid: string;
    name: string;
    service: string;
    valid_from: string;
    properties: {
      sources?: { name: string }[];
      input?: { name: string; service_reference?: { service: string; field: string } }[];
      output?: { name: string }[];
    };
  };

  // Define the paths to the YAML files
  let filePaths: string[] = [];

  let nodes = $state.raw<Node[]>([]);
  let edges = $state.raw<Edge[]>([]);

  const nodeTypes: any = {
    law: LawNode,
  };

  // Map service names to color indices (0-9)
  const serviceToColorIndex = new Map<string, number>();
  let nextColorIndex = 0;

  function getServiceColorIndex(service: string): number {
    if (!serviceToColorIndex.has(service)) {
      serviceToColorIndex.set(service, nextColorIndex % 7); // Limit to 7 colors (0-6)
      nextColorIndex++;
    }
    return serviceToColorIndex.get(service)!;
  }

  let laws = $state<Law[]>([]);
  let selectedLaws = $state<string[]>([]); // Contains the law UUIDs. This will hold the selected laws from the checkboxes

  (async () => {
    try {
      // Fetch the available laws from the backend
      const response = await fetch('/laws/list');
      filePaths = await response.json();

      let i = 0;

      const ns: Node[] = [];
      const es: Edge[] = [];

      // Initialize a map of (service, output_field) to their UUIDs
      const serviceOutputToUUIDsMap = new Map<string, string[]>();

      let allLaws = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content
          // @ts-expect-error ts(2345) // Seems like a bug in the type definitions of `resolve`
          const fileContent = await fetch(resolve(`/law/${filePath}`)).then((response) =>
            response.text(),
          );

          // Parse the YAML content
          const law = yaml.parse(fileContent) as Law;

          return law;
        }),
      );

      // Filter to keep only the latest version of each law (by service and name)
      const lawMap = new Map<string, Law>();
      for (const law of allLaws) {
        const key = `${law.service}:${law.name}`;
        const existing = lawMap.get(key);

        // Keep the law with the latest valid_from date (using string comparison)
        if (!existing || law.valid_from > existing.valid_from) {
          lawMap.set(key, law);
        }
      }

      laws = Array.from(lawMap.values());

      // Populate the map with the service+output combinations and their corresponding UUIDs
      for (const law of laws) {
        for (const output of law.properties.output || []) {
          const key = `${law.service}:${output.name}`;
          const current = serviceOutputToUUIDsMap.get(key);
          if (current) {
            serviceOutputToUUIDsMap.set(key, [...current, law.uuid]);
          } else {
            serviceOutputToUUIDsMap.set(key, [law.uuid]);
          }
        }
      }

      // Sort the laws (topological sort)
      laws.sort((a, b) => {
        return (
          (
            a.properties.input?.filter((input) => {
              const ref = input.service_reference;
              return ref && serviceOutputToUUIDsMap.has(`${ref.service}:${ref.field}`);
            }) || []
          ).length -
          (
            b.properties.input?.filter((input) => {
              const ref = input.service_reference;
              return ref && serviceOutputToUUIDsMap.has(`${ref.service}:${ref.field}`);
            }) || []
          ).length
        );
      });

      selectedLaws = laws.map((law) => law.uuid); // Initialize selected laws with all laws

      // First pass: create all nodes
      for (const data of laws) {
        const lawID = data.uuid;

        // Add parent nodes
        const colorIndex = getServiceColorIndex(data.service);
        ns.push({
          id: lawID,
          type: 'law',
          data: { label: `${data.service} — ${data.name}` }, // Algorithm name
          position: { x: i++ * 400, y: 0 },
          width: 340,
          height:
            Math.max(
              ((data.properties.sources?.length || 0) + (data.properties.input?.length || 0)) * 50 +
                70,
              (data.properties.output?.length || 0) * 50,
            ) + 120,
          class: `root service-${colorIndex}`,
        });

        // Sources
        const sourcesID = `${data.uuid}-sources`;

        ns.push({
          id: sourcesID,
          type: 'default',
          data: { label: 'Sources' },
          position: { x: 10, y: 60 },
          width: 150,
          height: (data.properties.sources?.length || 0) * 50 + 50,
          parentId: lawID,
          class: `property-group service-${colorIndex}`,
          draggable: false,
          selectable: false,
        });

        let j = 0;

        for (const source of data.properties.sources || []) {
          ns.push({
            id: `${data.uuid}-source-${source.name}`,
            type: 'input',
            sourcePosition: Position.Left,
            data: { label: source.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            height: 40,
            parentId: sourcesID,
            draggable: false,
            selectable: false,
          });
        }

        // Input
        const inputsID = `${data.uuid}-input`;

        ns.push({
          id: inputsID,
          type: 'default',
          data: { label: 'Input' },
          position: { x: 10, y: j * 50 + 130 },
          width: 150,
          height: (data.properties.input?.length || 0) * 50 + 50,
          parentId: lawID,
          class: `property-group service-${colorIndex}`,
          draggable: false,
          selectable: false,
        });

        j = 0;

        for (const input of data.properties.input || []) {
          const inputID = `${data.uuid}-input-${input.name}`;

          ns.push({
            id: inputID,
            type: 'input',
            sourcePosition: Position.Left,
            data: { label: input.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            height: 40,
            parentId: inputsID,
            extent: 'parent',
            draggable: false,
            selectable: false,
          });
        }

        // Output
        const outputsID = `${data.uuid}-output`;

        ns.push({
          id: outputsID,
          type: 'default',
          data: { label: 'Output' },
          position: { x: 180, y: 60 },
          width: 150,
          height: (data.properties.output?.length || 0) * 50 + 50,
          parentId: lawID,
          class: `property-group service-${colorIndex}`,
          draggable: false,
          selectable: false,
        });

        j = 0;

        for (const output of data.properties.output || []) {
          ns.push({
            id: `${data.uuid}-output-${output.name}`,
            type: 'output',
            targetPosition: Position.Right,
            data: { label: output.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            height: 40,
            parentId: outputsID,
            extent: 'parent',
            draggable: false,
            selectable: false,
          });
        }
      }

      // Second pass: create all edges now that all nodes exist
      for (const data of laws) {
        for (const input of data.properties.input || []) {
          const inputID = `${data.uuid}-input-${input.name}`;
          const ref = input.service_reference;

          if (ref) {
            const key = `${ref.service}:${ref.field}`;
            for (const uuid of serviceOutputToUUIDsMap.get(key) || []) {
              const target = `${uuid}-output-${ref.field}`;

              es.push({
                id: `${inputID}-${target}`,
                source: inputID,
                target: target,
                data: { refersToService: ref.service },
                type: 'bezier',
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  width: 20,
                  height: 40,
                },
                zIndex: 2,
              });
            }
          }
        }
      }

      // Add the nodes to the graph
      nodes = ns;

      // Add the edges to the graph
      edges = es;

      // Calculate initial positions
      calculatePositions();
    } catch (error) {
      console.error('Error reading file', error);
    }
  })();

  // Calculate positions for root nodes based on connections
  function calculatePositions() {
    // Filter for root nodes that are not hidden
    const rootNodes = nodes.filter((n) => n.class?.includes('root') && !n.hidden);

    // Build dependency graph: node -> nodes that depend on it
    const dependencyGraph = new Map<string, Set<string>>();
    const incomingCount = new Map<string, number>();

    // Initialize all nodes
    for (const node of rootNodes) {
      dependencyGraph.set(node.id, new Set());
      incomingCount.set(node.id, 0);
    }

    // Build the graph based on edges (source outputs -> target inputs)
    for (const edge of edges) {
      const sourceRoot = edge.source.substring(0, 36);
      const targetRoot = edge.target.substring(0, 36);

      if (sourceRoot !== targetRoot) {
        // Target depends on source, so target should be left of source (reversed)
        if (!dependencyGraph.has(sourceRoot)) {
          dependencyGraph.set(sourceRoot, new Set());
          incomingCount.set(sourceRoot, 0);
        }
        if (!dependencyGraph.has(targetRoot)) {
          dependencyGraph.set(targetRoot, new Set());
          incomingCount.set(targetRoot, 0);
        }

        // Only add if not already present (reversed: target -> source)
        if (!dependencyGraph.get(targetRoot)!.has(sourceRoot)) {
          dependencyGraph.get(targetRoot)!.add(sourceRoot);
          incomingCount.set(sourceRoot, (incomingCount.get(sourceRoot) || 0) + 1);
        }
      }
    }

    // Topological sort with layering
    const layers: string[][] = [];
    const nodeLayer = new Map<string, number>();
    const processed = new Set<string>();

    // Start with nodes that have no dependencies
    let currentLayer = rootNodes
      .map((n) => n.id)
      .filter((id) => (incomingCount.get(id) || 0) === 0);

    let layerIndex = 0;

    while (currentLayer.length > 0) {
      layers.push(currentLayer);

      for (const nodeId of currentLayer) {
        nodeLayer.set(nodeId, layerIndex);
        processed.add(nodeId);
      }

      // Find next layer: nodes whose dependencies are all processed
      const nextLayer = new Set<string>();
      for (const nodeId of currentLayer) {
        const dependents = dependencyGraph.get(nodeId) || new Set();
        for (const dependent of dependents) {
          if (processed.has(dependent)) continue;

          // Check if all dependencies of this dependent are processed (reversed)
          let allDepsProcessed = true;
          for (const edge of edges) {
            const sourceRoot = edge.source.substring(0, 36);
            const targetRoot = edge.target.substring(0, 36);
            if (sourceRoot === dependent && targetRoot !== sourceRoot) {
              if (!processed.has(targetRoot)) {
                allDepsProcessed = false;
                break;
              }
            }
          }

          if (allDepsProcessed) {
            nextLayer.add(dependent);
          }
        }
      }

      currentLayer = Array.from(nextLayer);
      layerIndex++;
    }

    // Add any remaining nodes (cycles or disconnected) to the last layer
    const unprocessed = rootNodes.map((n) => n.id).filter((id) => !processed.has(id));
    if (unprocessed.length > 0) {
      layers.push(unprocessed);
    }

    // Position nodes
    const nodeSpacing = 420;
    const layerSpacing = 100;
    const maxNodesPerColumn = 4;

    // Track the maximum column index used per layer to avoid overlaps
    const maxColumnPerLayer = new Map<number, number>();

    for (let l = 0; l < layers.length; l++) {
      const layer = layers[l];

      let visibleNodes = layer
        .map((nodeId) => ({
          nodeId,
          nodeIndex: nodes.findIndex((n) => n.id === nodeId),
        }))
        .filter(({ nodeIndex }) => nodeIndex !== -1 && !nodes[nodeIndex].hidden);

      let columnIndex = 0;
      let y = 0;
      let nodesInCurrentColumn = 0;

      for (const { nodeId, nodeIndex } of visibleNodes) {
        if (nodesInCurrentColumn >= maxNodesPerColumn) {
          // Move to next column
          columnIndex++;
          y = 0;
          nodesInCurrentColumn = 0;
        }

        // Calculate x position: add up all columns from previous layers plus current column
        let xOffset = 0;
        for (let prevLayer = 0; prevLayer < l; prevLayer++) {
          const maxCol = maxColumnPerLayer.get(prevLayer) || 0;
          xOffset += (maxCol + 1) * nodeSpacing;
        }
        const x = xOffset + columnIndex * nodeSpacing;

        nodes[nodeIndex] = {
          ...nodes[nodeIndex],
          position: { x, y },
        };

        y += (nodes[nodeIndex].height || 0) + layerSpacing;
        nodesInCurrentColumn++;
      }

      // Track the maximum column index used in this layer
      maxColumnPerLayer.set(l, columnIndex);
    }

    nodes = [...nodes]; // Force update for reactivity
  }

  function handleNodeClick({ node, event }: any) {
    // If the click is on a button.close, set the node and connected edges as hidden (using ID prefix matching)
    if ((event.target as HTMLElement).closest('.close')) {
      const lawUuid = node.id.substring(0, 36);

      nodes = nodes.map((n) => {
        if (n.id.startsWith(node.id)) {
          return { ...n, hidden: true };
        }
        return n;
      });

      edges = edges.map((e) => {
        if (e.source.startsWith(node.id) || e.target.startsWith(node.id)) {
          return { ...e, hidden: true };
        }
        return e;
      });

      // Remove from selectedLaws
      selectedLaws = selectedLaws.filter((uuid) => uuid !== lawUuid);
    }
  }

  // Handle changes to selectedLaws
  $effect(() => {
    // Note: empty code block to ensure the effect runs when selectedLaws changes (otherwise not triggered by Svelte)
    if (selectedLaws) {
    }

    // If no laws are selected, show all nodes and edges. IMPROVE: optimize this by updating selectedLaws, but avoiding infinite loop
    if (selectedLaws.length === 0) {
      nodes = untrack(() => nodes).map((n) => ({
        ...n,
        hidden: false,
      }));

      edges = untrack(() => edges).map((e) => ({
        ...e,
        hidden: false,
      }));
    } else {
      // Hide nodes that are not selected and not connected to any selected law
      nodes = untrack(() => nodes).map((node) => ({
        ...node,
        hidden:
          !selectedLaws.includes(node.id.substring(0, 36)) &&
          !untrack(() => edges).some(
            (edge) =>
              (edge.source.startsWith(node.id.substring(0, 36)) &&
                selectedLaws.includes(edge.target.substring(0, 36))) ||
              (edge.target.startsWith(node.id.substring(0, 36)) &&
                selectedLaws.includes(edge.source.substring(0, 36))),
          ),
      }));

      // Hide edges that are not connected to any selected law
      edges = untrack(() => edges).map((edge) => {
        return {
          ...edge,
          hidden:
            !selectedLaws.includes(edge.source.substring(0, 36)) &&
            !selectedLaws.includes(edge.target.substring(0, 36)),
        };
      });
    }
  });
</script>

<svelte:head>
  <title>Dependency graph — Burger.nl</title>
</svelte:head>

<div class="float-right h-screen w-80 overflow-y-auto px-6 pb-4 text-sm">
  <div class="sticky top-0 bg-white pt-6 pb-2">
  <h1 class="mb-3 text-base font-semibold">Selectie van wetten</h1>

    <button
      type="button"
      onclick={calculatePositions}
      class="cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-3 py-1.5 text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
      >Her-positioneer</button
    >
  </div>

  {#each Object.entries(laws.reduce((acc, law) => {
        if (!acc[law.service]) acc[law.service] = [];
        acc[law.service].push(law);
        return acc;
      }, {} as Record<string, Law[]>)) as [service, serviceLaws]}
    <h2
      class="service-{getServiceColorIndex(
        service,
      )} mb-2 mt-4 inline-block rounded-md px-2 py-1 text-sm font-semibold first:mt-0"
    >
      {service}
    </h2>
    {#each serviceLaws as law}
      <div class="mb-1.5">
        <label class="group inline-flex items-start">
          <input
            bind:group={selectedLaws}
            class="form-checkbox mr-1.5 mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            type="checkbox"
            value={law.uuid}
          />
          <span
            >{law.name}
            <button
              type="button"
              onclick={() => {
                selectedLaws = [law.uuid];
              }}
              class="invisible cursor-pointer font-semibold text-blue-700 hover:text-blue-800 group-hover:visible"
              >alleen</button
            ></span
          >
        </label>
      </div>
    {/each}
  {/each}
</div>

<!-- By default, the Svelte Flow container has a height of 100%. This means that the parent container needs a height to render the flow. -->
<div class="mr-80 h-screen">
  <SvelteFlow
    bind:nodes
    bind:edges
    {nodeTypes}
    onnodeclick={handleNodeClick}
    fitView
    nodesConnectable={false}
    proOptions={{
      hideAttribution: true,
    }}
    minZoom={0.1}
  >
    <Controls showLock={false} />
    <Background variant={BackgroundVariant.Dots} />
    <MiniMap zoomable pannable nodeColor={(n) => n.class?.includes('root') && !n.hidden ? '#ccc' : 'transparent'} />
  </SvelteFlow>
</div>

<style lang="postcss">
  @reference "tailwindcss/theme";

  :global(.root) {
    @apply rounded-md border border-black p-2;
  }
  
  /* Node colors, based on https://www.chartjs.org/docs/latest/general/colors.html. See also https://d3js.org/d3-scale-chromatic/categorical#categorical-schemes */
  :global(.service-0.root) {
    @apply bg-blue-50 border-blue-800;
  }

  :global(.service-0.property-group) {
    @apply bg-blue-100 border-blue-800;
  }

  :global(.service-1.root) {
    @apply bg-pink-50 border-pink-800;
  }

  :global(.service-1.property-group) {
    @apply bg-pink-100 border-pink-800;
  }

  :global(.service-2.root) {
    @apply bg-emerald-50 border-emerald-800;
  }

  :global(.service-2.property-group) {
    @apply bg-emerald-100 border-emerald-800;
  }

  :global(.service-3.root) {
    @apply bg-amber-50 border-amber-800;
  }

  :global(.service-3.property-group) {
    @apply bg-amber-100 border-amber-800;
  }

  :global(.service-4.root) {
    @apply bg-purple-50 border-purple-800;
  }

  :global(.service-4.property-group) {
    @apply bg-purple-100 border-purple-800;
  }

  :global(.service-5.root) {
    @apply bg-yellow-50 border-yellow-800;
  }

  :global(.service-5.property-group) {
    @apply bg-yellow-100 border-yellow-800;
  }

  :global(.service-6.root) {
    @apply bg-slate-50 border-slate-800;
  }

  :global(.service-6.property-group) {
    @apply bg-slate-100 border-slate-800;
  }

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

  :global(
    .property-group,
    .svelte-flow__node-input,
    .svelte-flow__node-source,
    .svelte-flow__node-output
  ) {
    @apply cursor-grab overflow-hidden text-ellipsis;
  }

  :global(.svelte-flow) {
    --xy-edge-stroke: #00a6f4; /* var(--color-sky-500); */
    --xy-edge-stroke-selected: #00a6f4; /* var(--color-sky-500); */
  }

  :global(.svelte-flow__arrowhead polyline) {
    @apply !fill-sky-500 !stroke-sky-500;
  }

  :global(.svelte-flow__edge.selected) {
    --xy-edge-stroke-width-default: 2.5;
  }
</style>
