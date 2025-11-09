<script lang="ts">
  import { type NodeProps, Handle, Position } from '@xyflow/svelte';

  type $$Props = NodeProps & {
    data: {
      label: string;
      layer: string;
      service: string;
      hasCircularDependency?: boolean;
    }
  };

  let { data }: $$Props = $props();

  // Define layer display names and colors
  const layerInfo: Record<string, { display: string, color: string }> = {
    'wet': { display: 'Wet', color: 'bg-blue-600 text-white' },
    'amvb': { display: 'AMvB', color: 'bg-indigo-500 text-white' },
    'regeling': { display: 'Regeling', color: 'bg-purple-500 text-white' },
    'beleidsregel': { display: 'Beleidsregel', color: 'bg-pink-500 text-white' },
    'werkinstructie': { display: 'Werkinstructie', color: 'bg-rose-400 text-white' },
  };

  const layer = layerInfo[data.layer] || { display: data.layer, color: 'bg-gray-500 text-white' };
</script>

<!-- Source handle (left side - provides data flowing left) -->
<Handle type="source" position={Position.Left} />

<div class="text-center p-2">
  <div class="mb-1 flex items-center justify-between gap-1">
    <span class="text-xs px-1.5 py-0.5 rounded {layer.color} font-medium">
      {layer.display}
    </span>
    <span class="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 font-medium">
      {data.service}
    </span>
  </div>
  <div class="text-sm font-semibold">{data.label}</div>
  {#if data.hasCircularDependency}
    <div class="mt-1 flex items-center justify-center gap-1" title="Deze wet heeft een circulaire afhankelijkheid (verwijst naar zichzelf)">
      <span class="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-800 border border-orange-300 font-medium">
        ↻ Circulair
      </span>
    </div>
  {/if}
</div>

<!-- Target handle (right side - receives data from the right) -->
<Handle type="target" position={Position.Right} />
