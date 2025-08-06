<script lang="ts">
  import { page } from '$app/state';
  import type { PageData } from './$types';
  import Prism from 'prismjs';
  const { highlight, languages } = Prism;
  import 'prismjs/components/prism-yaml';
  import 'prismjs/components/prism-diff';
  import 'prismjs/themes/prism-coy.css'; // IMPROVE: use some theme from https://github.com/PrismJS/prism-themes instead?
  import 'prismjs/plugins/diff-highlight/prism-diff-highlight';
  import 'prismjs/plugins/diff-highlight/prism-diff-highlight.css';

  export let data: PageData;
  const { id, compareId } = page.params;

  const lawA = data.laws.find((law) => law.uuid === id);
  const lawB = data.laws.find((law) => law.uuid === compareId);

  if (!lawA || !lawB) {
    throw new Error(`Law with id ${id} and/or ${compareId} not found`);
  }

  function createDiff(sourceA: string, sourceB: string): string {
    const linesA = sourceA.split('\n');
    const linesB = sourceB.split('\n');
    let diff = '';

    // Implementation of Longest Common Subsequence (LCS)
    function getLCS(a: string[], b: string[]): number[][] {
      const matrix: number[][] = Array(a.length + 1)
        .fill(null)
        .map(() => Array(b.length + 1).fill(0));

      for (let i = 1; i <= a.length; i++) {
        for (let j = 1; j <= b.length; j++) {
          if (a[i - 1] === b[j - 1]) {
            matrix[i][j] = matrix[i - 1][j - 1] + 1;
          } else {
            matrix[i][j] = Math.max(matrix[i - 1][j], matrix[i][j - 1]);
          }
        }
      }
      return matrix;
    }

    // Reconstruct the diff using the LCS matrix
    function reconstructDiff(
      matrix: number[][],
      a: string[],
      b: string[],
      i: number,
      j: number,
    ): string {
      if (i === 0 && j === 0) {
        return '';
      }

      if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
        // Line is unchanged
        return reconstructDiff(matrix, a, b, i - 1, j - 1) + `     ${a[i - 1]}\n`;
      } else if (j > 0 && (i === 0 || matrix[i][j - 1] >= matrix[i - 1][j])) {
        // Line was added
        return reconstructDiff(matrix, a, b, i, j - 1) + `+    ${b[j - 1]}\n`;
      } else if (i > 0 && (j === 0 || matrix[i][j - 1] < matrix[i - 1][j])) {
        // Line was removed
        return reconstructDiff(matrix, a, b, i - 1, j) + `-    ${a[i - 1]}\n`;
      }
      return '';
    }

    // Generate the diff using LCS
    const lcsMatrix = getLCS(linesA, linesB);
    return reconstructDiff(lcsMatrix, linesA, linesB, linesA.length, linesB.length);
  }

  const diffText = createDiff(lawA.source, lawB.source);
</script>

<svelte:head>
  <title>Vergelijk {lawA.name} met {lawB.name} — Law inspector — Burger.nl</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8">
  <h1 class="mb-2 text-3xl font-bold">{lawA.name}</h1>

  <a href="/" class="mb-6 inline-flex items-center text-blue-600 hover:text-blue-800">
    <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    Terug naar alle wetten
  </a>

  <p>Vergelijk met andere wet: TODO</p>

  <div class="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <h2 class="mb-2 text-lg font-semibold">Code</h2>

    <div class="mb-4 text-sm text-gray-600">
      <div class="mb-0.5 flex items-center">
        <span class="mr-2 inline-block h-4 w-4 rounded-sm bg-red-200"></span>
        <span>Verwijderd ten opzichte van {lawA.service}</span>
      </div>

      <div class="flex items-center">
        <span class="mr-2 inline-block h-4 w-4 rounded-sm bg-green-200"></span>
        <span>Toegevoegd in {lawB.service}</span>
      </div>
    </div>

    <pre
      class="diff-highlight !rounded-md !bg-gray-50 !px-4 !py-3 !text-sm/6 whitespace-pre-wrap"><code
        >{@html highlight(diffText, languages.diff, 'diff-yaml')}</code
      ></pre>
  </div>
</div>
