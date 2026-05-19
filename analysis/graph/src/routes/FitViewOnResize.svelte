<script lang="ts">
  import { useSvelteFlow } from '@xyflow/svelte';
  import { onMount } from 'svelte';

  // Refit the view whenever the containing element transitions from zero to
  // non-zero size. Needed because this app is embedded in an iframe inside a
  // tab that starts hidden (display:none via Alpine's x-show), which causes
  // SvelteFlow's initial fitView to run against a 0x0 container and lock the
  // viewport at minZoom with a negative translate.
  const { fitView } = $derived(useSvelteFlow());

  onMount(() => {
    const flow = document.querySelector('.svelte-flow') as HTMLElement | null;
    if (!flow) return;

    let lastWidth = flow.clientWidth;
    let lastHeight = flow.clientHeight;

    const ro = new ResizeObserver(() => {
      const w = flow.clientWidth;
      const h = flow.clientHeight;
      const grewFromZero = (lastWidth === 0 || lastHeight === 0) && w > 0 && h > 0;
      lastWidth = w;
      lastHeight = h;
      if (grewFromZero) {
        // Next frame so SvelteFlow has measured nodes in the resized container.
        requestAnimationFrame(() => fitView());
      }
    });
    ro.observe(flow);
    return () => ro.disconnect();
  });
</script>
