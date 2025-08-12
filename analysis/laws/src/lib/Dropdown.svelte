<script module lang="ts">
  export type Option = {
    value?: string;
    label: string;
    isHidden?: boolean;
  };
</script>

<script lang="ts">
  // Define props
  let {
    id = undefined,
    value = $bindable(),
    options = [],
    extraWrapperClasses = '',
    extraClasses = '',
    extraMenuClasses = '',
  }: {
    id: string | undefined;
    value: string | undefined;
    options: Option[];
    extraWrapperClasses: string;
    extraClasses: string;
    extraMenuClasses: string;
  } = $props();

  let isOpen = $state(false);

  function openMenu() {
    isOpen = true;
    document.body.addEventListener('click', closeMenu);
  }

  function closeMenu() {
    isOpen = false;
    document.body.removeEventListener('click', closeMenu);
  }
</script>

<div class="relative inline-block {extraWrapperClasses}">
  <button
    onclick={(e) => {
      e.stopPropagation();
      isOpen ? closeMenu() : openMenu();
    }}
    {id}
    class="inline-flex cursor-pointer items-center rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 hover:bg-gray-100 focus:border-blue-600 focus:ring-1 focus:ring-blue-600 {extraClasses}"
    type="button"
  >
    {options.find((el) => el.value === value)?.label}
    <svg class="ml-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
      ><path
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="m6 9l6 6l6-6"
      /></svg
    >
  </button>

  {#if isOpen}
    <div
      class="absolute top-10 left-0 z-20 max-h-80 min-w-full overflow-auto rounded-md border border-gray-200 bg-white {extraMenuClasses}"
    >
      {#each options.filter((el) => !el.isHidden) as option}
        <button
          onclick={(e) => {
            e.stopPropagation();
            value = option.value;
            closeMenu();
          }}
          type="button"
          class="block w-full px-3 py-2 text-left hover:bg-gray-100">{option.label}</button
        >
      {/each}
    </div>
  {/if}
</div>
