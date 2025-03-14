<script lang="ts">
  import { focusElement } from '$lib';
  import { tick } from 'svelte';
  import Markdown from 'svelte-exmarkdown';
  import { highlightPlugin } from './highlight-plugin';
  import 'highlight.js/styles/github-dark.css';
  // import PreWithCopyButton from './PreWithCopyButton.svelte';
  // const copyButtonPlugin = {
  //   renderer: { pre: PreWithCopyButton }
  // };

  type Message = {
    id: string;
    content: string;
    isOwn: boolean;
    timestamp: Date;
  };

  let messages: Message[] = [];
  let input = '';
  let messagesContainer: HTMLDivElement;
  let inputElement: HTMLInputElement;

  let quickReplies: string[] = [];

  // Initialize WebSocket connection
  const socket = new WebSocket('ws://localhost:8000/ws');

  // Connection opened
  socket.addEventListener('open', function (event) {
    console.log('Connected to server');
  });

  // Listen for messages
  socket.addEventListener('message', function (event) {
    // Parse the event data
    const data = JSON.parse(event.data) as { id: string; content: string; quick_replies: string[] };

    // If the message ID equals the ID of the previous message, append it to the previous message
    if (messages.length && messages[messages.length - 1].id === data.id) {
      messages[messages.length - 1].content += `${data.content}`; // IMPROVE: also look at earlier messages, since the user may post a message in between?
      messages = [...messages];
    } else {
      messages = [
        ...messages,
        {
          id: data.id,
          content: data.content,
          isOwn: false,
          timestamp: new Date(),
        },
      ]; // Note: instead of messages.push(...) to trigger Svelte reactivity, also below
    }

    // If the message contains quick replies, show them
    quickReplies = data.quick_replies || [];

    tick().then(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });
  });

  // Submit handler
  function handleSubmit() {
    if (input && socket.readyState === WebSocket.OPEN) {
      socket.send(input);

      messages = [
        ...messages,
        {
          id: '',
          content: input,
          isOwn: true,
          timestamp: new Date(),
        },
      ];
      input = '';
      quickReplies = [];

      tick().then(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      });
    }

    inputElement.focus();
  }
</script>

<svelte:head>
  <title>Machine law importer</title>
</svelte:head>

<main class="fixed left-0 top-0 flex h-full w-full flex-col px-6 py-4">
  <h1 class="mb-2 text-2xl">⚡️ Machine law importer</h1>

  <div
    bind:this={messagesContainer}
    class="mb-2 flex flex-grow flex-col overflow-y-auto scroll-smooth rounded-md bg-gray-100 p-4"
  >
    {#each messages as message}
      {#if message.isOwn}
        <div class="message own">{message.content}</div>
      {:else}
        <div class="message"><Markdown md={message.content} plugins={[highlightPlugin]} /></div>
      {/if}
    {/each}

    <div class="self-start">
      {#each quickReplies as quickReply}
        <button
          on:click={() => {
            input = quickReply;
            handleSubmit();
          }}
          class="mr-1.5 inline-flex cursor-pointer items-center rounded-full border border-blue-600 bg-white px-4 py-1 text-blue-600 hover:bg-blue-600 hover:text-white"
          type="button"
        >
          {#if quickReply === 'Ja'}
            <svg xmlns="http://www.w3.org/2000/svg" class="mr-1 h-4 w-4" viewBox="0 0 24 24"
              ><path
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="m5 12l5 5L20 7"
              /></svg
            >
          {:else if quickReply === 'Nee'}
            <svg xmlns="http://www.w3.org/2000/svg" class="mr-1 h-4 w-4" viewBox="0 0 24 24"
              ><path
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M18 6L6 18M6 6l12 12"
              /></svg
            >
          {/if}
          {quickReply}</button
        >
      {/each}
    </div>
  </div>

  <form class="mt-auto flex" on:submit|preventDefault={handleSubmit}>
    <input
      bind:this={inputElement}
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

  :global(.message a) {
    @apply text-blue-600 underline hover:text-blue-800 hover:no-underline;
  }

  :global(.message pre) {
    @apply overflow-x-auto rounded-sm bg-gray-900 px-3 py-2 text-sm text-white;
  }

  :global(pre code.hljs) {
    @apply !p-0 !bg-transparent;
  }
</style>
