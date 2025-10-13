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
  } from '@xyflow/svelte';
  import LawNode from './LawNode.svelte';

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  type Law = {
    uuid: string;
    name: string;
    service: string;
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

  let laws = $state<Law[]>([]);
  let selectedLaws = $state<string[]>([]); // Contains the law UUIDs. This will hold the selected laws from the checkboxes

  (async () => {
    try {
      // Fetch the available laws from the backend
      const response = await fetch('temp.json');
      filePaths = await response.json();

      let i = 0;

      const ns: Node[] = [];
      const es: Edge[] = [];

      // Initialize a map of service names to their UUIDs
      const serviceToUUIDsMap = new Map<string, string[]>();

      laws = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content
          // @ts-expect-error ts(2345) // Seems like a bug in the type definitions of `resolve`
          const fileContent = await fetch(resolve(`/law/${filePath}`)).then((response) =>
            response.text(),
          );

          // Parse the YAML content
          const law = yaml.parse(fileContent) as Law;

          // Populate the map with the service names and their corresponding UUIDs
          const current = serviceToUUIDsMap.get(law.service);
          if (current) {
            serviceToUUIDsMap.set(law.service, [...current, law.uuid]);
          } else {
            serviceToUUIDsMap.set(law.service, [law.uuid]);
          }

          return law;
        }),
      );

      // Sort the laws (topological sort)
      laws.sort((a, b) => {
        return (
          (
            a.properties.input?.filter((input) =>
              serviceToUUIDsMap.has(input.service_reference?.service as string),
            ) || []
          ).length -
          (
            b.properties.input?.filter((input) =>
              serviceToUUIDsMap.has(input.service_reference?.service as string),
            ) || []
          ).length
        );
      });

      selectedLaws = laws.map((law) => law.uuid); // Initialize selected laws with all laws

      for (const data of laws) {
        const lawID = data.uuid;

        // Add parent nodes
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
          class: 'root',
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
          class: 'property-group',
          draggable: false,
          selectable: false,
        });

        let j = 0;

        for (const source of data.properties.sources || []) {
          ns.push({
            id: `${data.uuid}-source-${source.name}`,
            type: 'input',
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
          class: 'property-group',
          draggable: false,
          selectable: false,
        });

        j = 0;

        for (const input of data.properties.input || []) {
          const inputID = `${data.uuid}-input-${input.name}`;

          ns.push({
            id: inputID,
            type: 'input',
            data: { label: input.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            height: 40,
            parentId: inputsID,
            extent: 'parent',
            draggable: false,
            selectable: false,
          });

          // If the input has a service reference, show it with an edge
          const ref = input.service_reference;
          if (ref) {
            for (const uuid of serviceToUUIDsMap.get(ref.service) || []) {
              const target = `${uuid}-output-${ref.field}`;
              // Check if target node exists. TODO: remove/improve, since most of the outputs will be added below?
              if (ns.some((n) => n.id === target)) {
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
              } else {
                console.warn(`Edge target node does not exist: ${target}`);
              }
            }
          }
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
          class: 'property-group',
          draggable: false,
          selectable: false,
        });

        j = 0;

        for (const output of data.properties.output || []) {
          ns.push({
            id: `${data.uuid}-output-${output.name}`,
            type: 'output',
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
    const rootNodes = nodes.filter((n) => n.class === 'root' && !n.hidden);
    const connectionGraph = new Map<string, Set<string>>();

    // Build connection graph between root nodes
    for (const edge of edges) {
      const sourceRoot = edge.source.substring(0, 36);
      const targetRoot = edge.target.substring(0, 36);

      if (sourceRoot !== targetRoot) {
        if (!connectionGraph.has(sourceRoot)) {
          connectionGraph.set(sourceRoot, new Set());
        }
        if (!connectionGraph.has(targetRoot)) {
          connectionGraph.set(targetRoot, new Set());
        }
        connectionGraph.get(sourceRoot)!.add(targetRoot);
        connectionGraph.get(targetRoot)!.add(sourceRoot);
      }
    }

    // Group nodes using a simple clustering approach
    const positioned = new Set<string>();
    const clusters: string[][] = [];

    for (const rootNode of rootNodes) {
      if (!positioned.has(rootNode.id)) {
        const cluster: string[] = [rootNode.id];
        positioned.add(rootNode.id);

        // Add connected nodes to the same cluster
        const toVisit = [rootNode.id];
        const visited = new Set<string>([rootNode.id]);

        while (toVisit.length > 0) {
          const current = toVisit.shift()!;
          const connections = connectionGraph.get(current) || new Set();

          for (const connected of connections) {
            if (!visited.has(connected)) {
              visited.add(connected);
              if (!positioned.has(connected)) {
                cluster.push(connected);
                positioned.add(connected);
                toVisit.push(connected);
              }
            }
          }
        }

        clusters.push(cluster);
      }
    }

    // Position clusters
    let clusterX = 0;
    const clusterSpacing = 100;
    const nodeSpacing = 420;

    for (const cluster of clusters) {
      // Sort cluster by connection count (most connected first)
      cluster.sort((a, b) => {
        const aConnections = connectionGraph.get(a)?.size || 0;
        const bConnections = connectionGraph.get(b)?.size || 0;
        return bConnections - aConnections;
      });

      const clusterWidth = Math.ceil(Math.sqrt(cluster.length));
      const rowHeights: number[] = [];

      // Calculate positions with dynamic row heights
      for (let i = 0; i < cluster.length; i++) {
        const nodeId = cluster[i];
        const nodeIndex = nodes.findIndex((n) => n.id === nodeId);

        if (nodeIndex !== -1) {
          const col = i % clusterWidth;
          const row = Math.floor(i / clusterWidth);

          // Calculate Y position based on previous rows
          let yPos = 0;
          for (let r = 0; r < row; r++) {
            yPos += rowHeights[r] + clusterSpacing;
          }

          nodes[nodeIndex] = {
            ...nodes[nodeIndex],
            position: { // Fully specify position for reactivity
              x: clusterX + col * nodeSpacing,
              y: yPos,
            },
          };

          // Track the maximum height in this row
          const nodeHeight = nodes[nodeIndex].height || 0;
          if (!rowHeights[row]) {
            rowHeights[row] = nodeHeight;
          } else {
            rowHeights[row] = Math.max(rowHeights[row], nodeHeight);
          }
        }
      }

      clusterX += clusterWidth * nodeSpacing + clusterSpacing;
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

      // If no laws are visible anymore, show all laws
      if (selectedLaws.length === 0) {
        selectedLaws = laws.map((law) => law.uuid);

        nodes = nodes.map((n) => ({
          ...n,
          hidden: false,
        }));

        edges = edges.map((e) => ({
          ...e,
          hidden: false,
        }));
      }
    }
  }

  $effect(() => {
    if (nodes) {
      console.log('Nodes count:', nodes.length);
    }
  });

  // Handle changes to selectedLaws
  $effect(() => {
    // Note: empty code block to ensure the effect runs when selectedLaws changes (otherwise not triggered by Svelte)
    if (selectedLaws) {
    }

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
  });
</script>

<svelte:head>
  <title>Dependency graph — Burger.nl</title>
</svelte:head>

<div class="float-right h-screen w-80 overflow-y-auto px-6 py-4 text-sm">
  <h1 class="mb-3 text-base font-semibold">Selectie van wetten</h1>

  <button
    type="button"
    onclick={calculatePositions}
    class="mb-3 inline-block cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-3 py-1.5 text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
    >Her-positioneer</button
  >

  {#each laws as law}
    <div class="mb-1.5">
      <label class="group inline-flex items-start">
        <input
          bind:group={selectedLaws}
          class="form-checkbox mt-0.5 mr-1.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          type="checkbox"
          value={law.uuid}
        />
        <span
          >{law.name} <span class="text-xs text-gray-600">({law.service})</span>
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
    <MiniMap zoomable pannable />
  </SvelteFlow>
</div>

<style lang="postcss">
  @reference "tailwindcss/theme";

  :global(.property-group) {
    @apply bg-blue-100;
  }

  :global(
    .property-group,
    .svelte-flow__node-input,
    .svelte-flow__node-source,
    .svelte-flow__node-output
  ) {
    @apply cursor-grab;
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
