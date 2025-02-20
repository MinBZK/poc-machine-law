<script lang="ts">
  import { focusElement } from '$lib';

  type Message = {
    content: string;
    isOwn: boolean;
    timestamp: Date;
  };

  let messages: Message[] = [];
  let input = '';

  // Initialize WebSocket connection
  const socket = new WebSocket('ws://localhost:8000/ws');

  // Connection opened
  socket.addEventListener('open', function (event) {
    console.log('Connected to server');
  });

  // Listen for messages
  socket.addEventListener('message', function (event) {
    messages = [
      ...messages,
      {
        content: event.data,
        isOwn: false,
        timestamp: new Date(),
      },
    ]; // Note: instead of messages.push(...) to trigger Svelte reactivity, also below
  });

  // Submit handler
  function handleSubmit() {
    if (input && socket.readyState === WebSocket.OPEN) {
      socket.send(input);
      messages = [
        ...messages,
        {
          content: input,
          isOwn: true,
          timestamp: new Date(),
        },
      ];
      input = '';
    }
  }
</script>

<svelte:head>
  <title>Machine law importer</title>
</svelte:head>

<main class="fixed left-0 top-0 flex h-full w-full flex-col px-6 py-4">
  <h1 class="mb-2 text-2xl">⚡️ Machine law importer</h1>

  <div class="mb-2 flex flex-grow flex-col overflow-y-auto rounded-md bg-gray-100 p-4">
    {#each messages as message}
      <div class="message" class:own={message.isOwn}>{message.content}</div>
    {/each}
  </div>

  <form class="mt-auto flex" on:submit|preventDefault={handleSubmit}>
    <input
      bind:value={input}
      use:focusElement
      class="mr-2 block w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-800 focus:border-blue-500 focus:ring-blue-500"
      type="text"
      placeholder="Type a message…"
    />

    <button
      class="inline-block rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
      type="submit"
      aria-label="Send message"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
        ><path
          fill="none"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4.698 4.034L21 12L4.698 19.966a.5.5 0 0 1-.546-.124a.56.56 0 0 1-.12-.568L6.5 12L4.032 4.726a.56.56 0 0 1 .12-.568a.5.5 0 0 1 .546-.124M6.5 12H21"
        /></svg
      >
    </button>
  </form>
</main>

<style lang="postcss">
  @reference "tailwindcss/theme";

  .message {
    @apply mb-3 max-w-[75%] self-start whitespace-pre-line rounded-md bg-white px-3 py-2;

    &.own {
      @apply self-end bg-green-100;
    }
  }
</style>
