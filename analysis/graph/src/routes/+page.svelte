<script lang="ts">
  import { writable } from 'svelte/store';
  import yaml from 'yaml';
  import { base } from '$app/paths';
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

  const nodes = writable<Node[]>([]);
  const edges = writable<Edge[]>([]);

  const nodeTypes: any = {
    law: LawNode,
  };

  let laws: Law[] = [];
  let selectedLaws: string[] = []; // Contains the law UUIDs. This will hold the selected laws from the checkboxes

  (async () => {
    try {
      // Fetch the available laws from the backend
      const response = await fetch('/laws/list');
      filePaths = await response.json();

      let i = 0;

      const ns: Node[] = [];
      const es: Edge[] = [];

      // Initialize a map of service names to their UUIDs
      const serviceToUUIDsMap = new Map<string, string[]>();

      laws = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content
          const fileContent = await fetch(`${base}/law/${filePath}`).then((response) =>
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
          data: { label: data.name }, // Algorithm name
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
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        let j = 0;

        for (const source of data.properties.sources || []) {
          ns.push({
            id: `${data.uuid}-source-${source.name}`,
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
        const inputsID = `${data.uuid}-input`;

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
          const inputID = `${data.uuid}-input-${input.name};`;

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
            for (const uuid of serviceToUUIDsMap.get(ref.service) || []) {
              const target = `${uuid}-output-${ref.field}`;
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
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        j = 0;

        for (const output of data.properties.output || []) {
          ns.push({
            id: `${data.uuid}-output-${output.name}`,
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

      // Add the edges to the graph
      $edges = es;
    } catch (error) {
      console.error('Error reading file', error);
    }
  })();

  function handleNodeClick(event: CustomEvent<{ event: MouseEvent | TouchEvent; node: Node }>) {
    // If the click is on a button.close, remove the node. IMPROVE: remove the child nodes first
    if ((event.detail.event.target as HTMLElement).closest('.close')) {
      const node = event.detail.node;

      // Remove the node and all its children (using ID prefix matching)
      $nodes = $nodes.filter((n) => !n.id.startsWith(node.id));

      // Remove all edges connected to the removed nodes
      $edges = $edges.filter((e) => !e.source.startsWith(node.id) && !e.target.startsWith(node.id));
    }
  }

  // Handle changes to selectedLaws
  $: ((selectedLaws: string[]) => {
    // Hide nodes that are not selected and not connected to any selected law
    $nodes = $nodes.map((node) => ({
      ...node,
      hidden:
        !selectedLaws.includes(node.id.substring(0, 36)) &&
        !$edges.some(
          (edge) =>
            (edge.source.startsWith(node.id.substring(0, 36)) &&
              selectedLaws.includes(edge.target.substring(0, 36))) ||
            (edge.target.startsWith(node.id.substring(0, 36)) &&
              selectedLaws.includes(edge.source.substring(0, 36))),
        ),
    }));

    // Hide edges that are not connected to any selected law
    $edges = $edges.map((edge) => {
      return {
        ...edge,
        hidden:
          !selectedLaws.includes(edge.source.substring(0, 36)) &&
          !selectedLaws.includes(edge.target.substring(0, 36)),
      };
    });
  })(selectedLaws);
</script>

<svelte:head>
  <title>Dependency graph — Digilab</title>
</svelte:head>

<div class="float-right h-screen w-80 overflow-y-auto px-6 py-4 text-sm">
  <h1 class="mb-3 text-base font-semibold">Selectie van wetten</h1>

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
            on:click|preventDefault={() => {
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
    {nodes}
    {edges}
    {nodeTypes}
    on:nodeclick={handleNodeClick}
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
