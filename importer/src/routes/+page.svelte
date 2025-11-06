<script lang="ts">
  import { focusElement } from '$lib';
  import { tick } from 'svelte';
  import Markdown from 'svelte-exmarkdown';
  import { highlightPlugin } from './highlight-plugin';
  import 'highlight.js/styles/github-dark.css';
  import PreWithCopyButton from './PreWithCopyButton.svelte';
  import { browser } from '$app/environment';

  const copyButtonPlugin = {
    renderer: { pre: PreWithCopyButton },
  };

  type Message = {
    id: string;
    content: string;
    isOwn: boolean;
    timestamp: Date;
  };

  let anthropicApiKey = browser ? localStorage.getItem('anthropic-api-key') || '' : '';
  let tavilyApiKey = browser ? localStorage.getItem('tavily-api-key') || '' : '';
  let anthropicAvailableViaEnv = false;
  let tavilyAvailableViaEnv = false;
  let apiFormIsShown = false;
  let anthropicApiKeyInput: HTMLInputElement | undefined;

  // Check which API keys are available via environment variables
  async function checkApiKeysStatus() {
    try {
      const response = await fetch('/importer/api-keys-status');
      const data = await response.json();
      anthropicAvailableViaEnv = data.anthropic_available;
      tavilyAvailableViaEnv = data.tavily_available;
      
      // Show form only if at least one key is needed and not available via env
      const needsAnthropicKey = !anthropicAvailableViaEnv && anthropicApiKey === '';
      const needsTavilyKey = !tavilyAvailableViaEnv && tavilyApiKey === '';
      apiFormIsShown = needsAnthropicKey || needsTavilyKey;
    } catch (error) {
      console.error('Failed to check API keys status:', error);
      // Fallback to showing form if we can't check
      apiFormIsShown = anthropicApiKey === '' || tavilyApiKey === '';
    }
  }

  // Check API keys status on component mount
  if (browser) {
    checkApiKeysStatus();
  }

  let messages: Message[] = [];
  let input = '';
  let messagesContainer: HTMLDivElement;
  let inputElement: HTMLInputElement;

  let quickReplies: string[] = [];

  let progress = 0;

  let messageIdToIgnore: string | undefined;

  // Loading / busy indicator
  let isLoading = false;

  function handleKeySubmit() {
    if (browser) {
      localStorage.setItem('anthropic-api-key', anthropicApiKey);
      localStorage.setItem('tavily-api-key', tavilyApiKey);
    }

    // Send the keys to the server (only send non-empty keys)
    const keysToSend: any = { type: 'keys' };
    if (!anthropicAvailableViaEnv && anthropicApiKey) {
      keysToSend.anthropicApiKey = anthropicApiKey;
    }
    if (!tavilyAvailableViaEnv && tavilyApiKey) {
      keysToSend.tavilyApiKey = tavilyApiKey;
    }
    
    socket.send(JSON.stringify(keysToSend));
    apiFormIsShown = false;
  }

  // Initialize WebSocket connection
  const socket = new WebSocket('/importer/ws');

  // Connection opened
  socket.addEventListener('open', function (event) {
    console.log('Connected to server');

    // If the API keys are already set, send them to the server
    const keysToSend: any = { type: 'keys' };
    let hasKeys = false;
    
    if (!anthropicAvailableViaEnv && anthropicApiKey) {
      keysToSend.anthropicApiKey = anthropicApiKey;
      hasKeys = true;
    }
    if (!tavilyAvailableViaEnv && tavilyApiKey) {
      keysToSend.tavilyApiKey = tavilyApiKey;
      hasKeys = true;
    }
    
    if (hasKeys) {
      socket.send(JSON.stringify(keysToSend));
    }
  });

  // Listen for messages
  socket.addEventListener('message', function (event) {
    // Parse the event data
    const data = JSON.parse(event.data) as {
      id: string;
      type?: string;
      content: string | number;
      quick_replies: string[];
    };

    // If the message is a progress update, update the progress
    if (data.type === 'progress') {
      progress = data.content as number;
      return;
    }

    // If the message ID equals the ID of the previous message, append it to the previous message
    if (data.id === messageIdToIgnore) {
      return; // Skip this message
    }

    if (messages.length && messages[messages.length - 1].id === data.id) {
      messages[messages.length - 1].content += `${data.content}`; // IMPROVE: also look at earlier messages, since the user may post a message in between?
      messages = [...messages];
    } else {
      isLoading = false; // Clear loading state

      messages = [
        ...messages,
        {
          id: data.id,
          content: data.content as string,
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
      if (
        input.toLocaleLowerCase() === 'stop' &&
        messages.length &&
        messages[messages.length - 1].id
      ) {
        // Abort the current processing (note: only client-side, see the comments in the backend code). IMPROVE: improve this functionality, use a button that is only visible when streaming, etc.
        input = '';
        messageIdToIgnore = messages[messages.length - 1].id;

        return;
      }

      isLoading = true; // Set loading state
      socket.send(JSON.stringify({ type: 'text', content: input }));

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
  <title>Wet-importer</title>
</svelte:head>

<main class="fixed left-0 top-0 flex h-full w-full flex-col px-6 py-4">
  <h1 class="mb-2.5 flex items-center gap-2.5 text-2xl font-medium">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-blue-600" viewBox="0 0 24 24"
      ><path
        fill="currentColor"
        fill-rule="evenodd"
        d="M12 2.25a.75.75 0 0 1 .75.75v.756a49 49 0 0 1 9.152 1a.75.75 0 0 1-.152 1.485h-1.918l2.474 10.124a.75.75 0 0 1-.375.84A6.7 6.7 0 0 1 18.75 18a6.7 6.7 0 0 1-3.181-.795a.75.75 0 0 1-.375-.84l2.474-10.124H12.75v13.28c1.293.076 2.534.343 3.697.776a.75.75 0 0 1-.262 1.453h-8.37a.75.75 0 0 1-.262-1.453c1.162-.433 2.404-.7 3.697-.775V6.24H6.332l2.474 10.124a.75.75 0 0 1-.375.84A6.7 6.7 0 0 1 5.25 18a6.7 6.7 0 0 1-3.181-.795a.75.75 0 0 1-.375-.84L4.168 6.241H2.25a.75.75 0 0 1-.152-1.485a49 49 0 0 1 9.152-1V3a.75.75 0 0 1 .75-.75m4.878 13.543l1.872-7.662l1.872 7.662zm-9.756 0L5.25 8.131l-1.872 7.662z"
        clip-rule="evenodd"
      /></svg
    > Wet-importer
  </h1>

  {#if apiFormIsShown}
    <form
      on:submit|preventDefault={handleKeySubmit}
      class="mb-5 grid grid-cols-5 gap-4 rounded-md border border-gray-300 bg-gray-50 p-4"
    >
      {#if !anthropicAvailableViaEnv}
        <div class="col-span-2 flex flex-col">
          <label class="mb-2 inline-block font-medium" for="api-key">Claude / Anthropic API key</label
          >

          <input
            bind:value={anthropicApiKey}
            bind:this={anthropicApiKeyInput}
            placeholder="sk-…"
            id="api-key"
            type="text"
            class="mt-auto block w-full rounded-md border border-gray-300 bg-white px-2.5 py-2 focus:border-blue-500 focus:ring-blue-500"
            autocomplete="off"
          />
        </div>
      {:else}
        <div class="col-span-2 flex flex-col">
          <span class="mb-2 inline-block font-medium">Claude / Anthropic API key</span>
          <div class="flex items-center rounded-md border border-emerald-300 bg-emerald-50 px-2.5 py-2 h-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="mr-2 h-4 w-4 text-emerald-600" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0"/><path d="m9 12l2 2l4-4"/></g></svg>
            <span class="text-sm text-emerald-700">Ingesteld via omgevingsvariable</span>
          </div>
        </div>
      {/if}

      {#if !tavilyAvailableViaEnv}
        <div class="col-span-2 flex flex-col">
          <label class="mb-2 inline-block font-medium" for="tavily-api-key">Tavily API key</label>

          <input
            bind:value={tavilyApiKey}
            placeholder="tvly-…"
            id="tavily-api-key"
            type="text"
            class="mt-auto block w-full rounded-md border border-gray-300 bg-white px-2.5 py-2 focus:border-blue-500 focus:ring-blue-500"
            autocomplete="off"
          />
        </div>
      {:else}
        <div class="col-span-2 flex flex-col">
          <span class="mb-2 inline-block font-medium">Tavily API key</span>
          <div class="flex items-center rounded-md border border-emerald-300 bg-emerald-50 px-2.5 py-2 h-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="mr-2 h-4 w-4 text-emerald-600" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0"/><path d="m9 12l2 2l4-4"/></g></svg>
            <span class="text-sm text-emerald-700">Ingesteld via omgevingsvariable</span>
          </div>
        </div>
      {/if}

      {#if !anthropicAvailableViaEnv || !tavilyAvailableViaEnv}
        <button
          type="submit"
          class="mt-auto cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
        >
          Gebruiken
        </button>
      {:else}
        <button
          type="button"
          on:click={() => apiFormIsShown = false}
          class="mt-auto cursor-pointer rounded-md border border-gray-600 bg-gray-600 px-4 py-2 text-white transition duration-200 hover:border-gray-700 hover:bg-gray-700"
        >
          Sluiten
        </button>
      {/if}

      <small class="col-span-5 text-sm text-gray-600">
        {#if !anthropicAvailableViaEnv || !tavilyAvailableViaEnv}
          Verplicht, worden niet opgeslagen, alleen in de browser. Meer informatie:
          {#if !anthropicAvailableViaEnv}
            <a
              class="text-blue-700 underline hover:no-underline"
              href="https://console.anthropic.com/"
              target="_blank"
              rel="nofollow">Anthropic</a
            >{#if !tavilyAvailableViaEnv}, {/if}
          {/if}
          {#if !tavilyAvailableViaEnv}
            <a
              class="text-blue-700 underline hover:no-underline"
              href="https://tavily.com/#faq"
              target="_blank"
              rel="nofollow">Tavily</a
            >
          {/if}.
        {:else}
          Alle API keys zijn ingesteld via omgevingsvariabelen.
        {/if}
      </small>
    </form>
  {:else if !anthropicAvailableViaEnv || !tavilyAvailableViaEnv}
    <div
      class="mb-5 flex items-center rounded-md border border-emerald-700/25 bg-emerald-50 px-3 py-2"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mr-1.5 h-5 w-5 text-emerald-600"
        viewBox="0 0 24 24"
        ><g
          fill="none"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          ><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0" /><path d="m9 12l2 2l4-4" /></g
        ></svg
      >
      {#if anthropicAvailableViaEnv}
        Claude / Anthropic API key ingesteld via omgevingsvariabele, Tavily API key via browser
      {:else if tavilyAvailableViaEnv}
        Tavily API key ingesteld via omgevingsvariabele, Claude / Anthropic API key via browser
      {:else}
        Claude / Anthropic en Tavily API keys ingesteld via browser
      {/if}

      <button
        on:click={async () => {
          apiFormIsShown = true;
          await tick();
          anthropicApiKeyInput?.focus();
        }}
        type="button"
        class="ml-3 cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-2 py-1 text-sm text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
      >
        Aanpassen
      </button>
    </div>
  {/if}

  <div class="grid min-h-0 flex-grow grid-cols-3 gap-4">
    <div
      bind:this={messagesContainer}
      class="col-span-2 mb-2 flex flex-col overflow-y-auto scroll-smooth rounded-md bg-gray-100 p-4"
    >
      {#each messages as message}
        {#if message.isOwn}
          <div class="message own">{message.content}</div>
        {:else}
          <div class="message">
            <Markdown
              md={message.content as string}
              plugins={[highlightPlugin, copyButtonPlugin]}
            />
          </div>
        {/if}
      {/each}

      {#if isLoading}
        <div class="message flex items-center gap-2">
          <svg
            class="h-5 w-5 animate-spin text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
            ></circle>
            <path
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span class="text-sm text-gray-600">Bericht wordt gegenereerd…</span>
        </div>
      {/if}

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

    <div class="mb-2 overflow-y-auto">
      <ol class="relative ml-4 border-s border-gray-200 text-gray-500">
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full ring-4 ring-white {progress >=
            1
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-gray-100 text-gray-600'}"
          >
            {#if progress >= 1}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m5 12l5 5L20 7"
                /></svg
              >
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
                ><path
                  fill="currentColor"
                  d="m12.999 2l-.001 1.278l5 1.668l3.633-1.21l.632 1.896l-3.031 1.011l3.095 8.512A5.98 5.98 0 0 1 17.998 17a5.98 5.98 0 0 1-4.328-1.845l3.094-8.512l-3.766-1.256V19h4v2h-10v-2h4V5.387L7.232 6.643l3.095 8.512A5.98 5.98 0 0 1 6 17a5.98 5.98 0 0 1-4.33-1.845l3.095-8.512l-3.03-1.01l.632-1.898L6 4.945l4.999-1.667V2zm5 7.103l-1.959 5.386a4 4 0 0 0 1.959.511c.7 0 1.37-.18 1.958-.51zm-12 0L4.04 14.489A4 4 0 0 0 5.999 15c.7 0 1.37-.18 1.958-.51z"
                /></svg
              >
            {/if}
          </span>
          <h3 class="font-medium leading-tight">Wetnaam</h3>
          <p class="text-sm">Identificatie van de wet</p>
        </li>
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full ring-4 ring-white {progress >=
            2
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-gray-100 text-gray-600'}"
          >
            {#if progress >= 2}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m5 12l5 5L20 7"
                /></svg
              >
            {:else}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-gray-500"
                viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m9 15l6-6m-4-3l.463-.536a5 5 0 0 1 7.071 7.072L18 13m-5 5l-.397.534a5.07 5.07 0 0 1-7.127 0a4.97 4.97 0 0 1 0-7.071L6 11"
                /></svg
              >
            {/if}
          </span>
          <h3 class="font-medium leading-tight">Wet URL</h3>
          <p class="text-sm">Plek waar de wet online staat</p>
        </li>
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full ring-4 ring-white {progress >=
            3
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-gray-100 text-gray-600'}"
          >
            {#if progress >= 3}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m5 12l5 5L20 7"
                /></svg
              >
            {:else}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-gray-500"
                viewBox="0 0 24 24"
                ><g
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  ><path
                    d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
                  /><path
                    d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2m0 9h.01M9 17h.01M12 16l1 1l3-3"
                  /></g
                ></svg
              >
            {/if}
          </span>
          <h3 class="font-medium leading-tight">Controle</h3>
          <p class="text-sm">Controle of de output voldoet</p>
        </li>
        <li class="ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full ring-4 ring-white {progress >=
            4
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-gray-100 text-gray-600'}"
          >
            {#if progress >= 4}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m5 12l5 5L20 7"
                /></svg
              >
            {:else}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-gray-500"
                viewBox="0 0 24 24"
                ><g
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  ><path
                    d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
                  /><path
                    d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2m0 9l2 2l4-4"
                  /></g
                ></svg
              >
            {/if}
          </span>
          <h3 class="font-medium leading-tight">Output</h3>
          <p class="text-sm">Model van de wet in YAML-formaat</p>
        </li>
      </ol>
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
      class="inline-block cursor-pointer rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
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

  :global(pre code.hljs) {
    @apply !bg-transparent !p-0;
  }
</style>
