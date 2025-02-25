<script lang="ts">
  import { writable } from 'svelte/store';
  import yaml from 'yaml';
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

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  // Define the paths to the YAML files
  const filePaths = [
    '/law/wet_inkomstenbelasting/BELASTINGDIENST-2001-01-01.yaml',
    '/law/wet_inkomstenbelasting/UWV-2020-01-01.yaml',
    '/law/zvw/RVZ-2024-01-01.yaml',
    '/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml',
  ];

  const nodes = writable<Node[]>([]);
  const edges = writable<Edge[]>([]);

  (async () => {
    try {
      let i = 0;

      const ns: Node[] = [];
      const es: Edge[] = [];

      // Initialize a Set to store unique service names
      const uniqueServices = new Set<string>();

      for (const filePath of filePaths) {
        // Read the file content
        const fileContent = await fetch(filePath).then((response) => response.text());

        // Parse the YAML content
        const data = yaml.parse(fileContent);

        // console.log('data', data);

        // Add the service name to the Set of unique services
        uniqueServices.add(data.service);

        const lawID = data.uuid;

        // Add parent nodes
        ns.push({
          id: lawID,
          type: 'default',
          data: { label: data.name }, // Algorithm name
          position: { x: i++ * 400, y: 0 },
          width: 340,
          height:
            Math.max(
              ((data.properties.sources?.length || 0) + (data.properties.input?.length || 0)) * 50 + 70,
              (data.properties.output?.length || 0) * 50,
            ) +
            120,
          class: 'root',
        });

        // Sources
        const sourcesID = `${data.service}-sources`;

        ns.push({
          id: sourcesID,
          type: 'default',
          data: { label: 'Sources' },
          position: { x: 10, y: 60 },
          width: 150,
          height: (data.properties.sources?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        let j = 0;

        for (const source of data.properties.sources || []) {
          ns.push({
            id: `${data.service}-source-${source.name}`,
            type: 'input',
            data: { label: source.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: sourcesID,
            extent: 'parent',
            expandParent: true,
          });
        }

        // Input
        const inputsID = `${data.service}-input`;

        ns.push({
          id: inputsID,
          type: 'default',
          data: { label: 'Input' },
          position: { x: 10, y: j * 50 + 130 },
          width: 150,
          height: (data.properties.input?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        j = 0;

        for (const input of data.properties.input || []) {
          const inputID = `${data.service}-input-${input.name};`;

          ns.push({
            id: inputID,
            type: 'input',
            data: { label: input.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: inputsID,
            extent: 'parent',
            expandParent: true,
          });

          // If the input has a service reference, show it with an edge
          const ref = input.service_reference;
          if (ref) {
            const target = `${ref.service}-output-${ref.field}`;
            es.push({
              id: `${inputID}-${target}`,
              source: inputID,
              target: target,
              data: { refersToService: ref.service },
              type: 'bezier',
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
              zIndex: 1,
            });
          }
        }

        // Output
        const outputsID = `${data.service}-output`;

        ns.push({
          id: outputsID,
          type: 'default',
          data: { label: 'Output' },
          position: { x: 180, y: 60 },
          width: 150,
          height: (data.properties.output?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        j = 0;

        for (const output of data.properties.output || []) {
          ns.push({
            id: `${data.service}-output-${output.name}`,
            type: 'output',
            data: { label: output.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: outputsID,
            extent: 'parent',
            expandParent: true,
          });
        }
      }

      // Add the nodes to the graph
      $nodes = ns;

      // Add the edges to the graph, but only those that refer to services that are in the Set of unique services
      $edges = es.filter((edge) => uniqueServices.has(edge.data!.refersToService as string));
    } catch (error) {
      console.error('Error reading file', error);
    }
  })();
</script>

<svelte:head>
  <title>Dependency graph — Digilab</title>
</svelte:head>

<!--
👇 By default, the Svelte Flow container has a height of 100%.
This means that the parent container needs a height to render the flow.
-->
<div class="h-screen">
  <SvelteFlow
    {nodes}
    {edges}
    fitView
    nodesConnectable={false}
    proOptions={{
      hideAttribution: true,
    }}
    minZoom={0.2}
  >
    <Controls showLock={false} />
    <Background variant={BackgroundVariant.Dots} />
    <MiniMap zoomable pannable />
  </SvelteFlow>
</div>

<style lang="postcss">
  :global(.root) {
    @apply bg-blue-50;
  }

  :global(.property-group) {
    @apply bg-blue-100;
  }

  :global(.svelte-flow) {
    --xy-edge-stroke: #0284c7; /* var(--color-blue-600); */
    --xy-edge-stroke-selected: #0284c7; /* var(--color-blue-600); */
  }

  :global(.svelte-flow__arrowhead polyline) {
    @apply fill-blue-600 stroke-blue-600;
  }

  :global(.svelte-flow__edge.selected) {
    --xy-edge-stroke-width-default: 2.5;
  }
</style>
