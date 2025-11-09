import { toPng } from 'html-to-image';
import { jsPDF } from 'jspdf';

export interface Node {
  position: { x: number; y: number };
  width?: number;
  height?: number;
  hidden?: boolean;
}

/**
 * Calculate the bounding box of all visible nodes
 */
export function calculateBounds(nodes: Node[], padding: number = 50) {
  const visibleNodes = nodes.filter(n => !n.hidden);

  if (visibleNodes.length === 0) {
    return null;
  }

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  for (const node of visibleNodes) {
    const x = node.position.x;
    const y = node.position.y;
    const width = node.width || 280;
    const height = node.height || 100;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + width);
    maxY = Math.max(maxY, y + height);
  }

  minX -= padding;
  minY -= padding;
  maxX += padding;
  maxY += padding;

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY
  };
}

/**
 * Export the viewport to PNG
 */
export async function exportViewportToPng(
  nodes: Node[],
  baseFilename: string = 'graph'
): Promise<void> {
  // Debug: Log the DOM structure
  const flowContainer = document.querySelector('.svelte-flow');
  console.log('=== DOM Structure Debug ===');
  console.log('Flow container found:', !!flowContainer);
  if (flowContainer) {
    const children = Array.from(flowContainer.children).map(el => el.className);
    console.log('Flow container children:', children);
  }

  const viewport = document.querySelector('.svelte-flow__viewport');
  if (!viewport) {
    throw new Error('Viewport not found');
  }
  console.log('Viewport children:', Array.from(viewport.children).map(el => el.className));

  // Check for edges specifically
  const edgeElements = document.querySelectorAll('.svelte-flow__edge, [class*="edge"]');
  console.log('Edge elements found:', edgeElements.length);
  console.log('Edge parent elements:', Array.from(edgeElements).slice(0, 3).map(el => el.parentElement?.className));

  const bounds = calculateBounds(nodes);
  if (!bounds) {
    throw new Error('No visible nodes to export');
  }

  const viewportElement = viewport as HTMLElement;

  // html-to-image options that properly handle SVG elements (edges)
  const dataUrl = await toPng(viewportElement, {
    backgroundColor: '#ffffff',
    width: bounds.width,
    height: bounds.height,
    pixelRatio: 2,
    cacheBust: true,
    style: {
      width: `${bounds.width}px`,
      height: `${bounds.height}px`,
      transform: `translate(${-bounds.minX}px, ${-bounds.minY}px)`,
    }
  });

  const filename = `${baseFilename}-${new Date().toISOString().split('T')[0]}.png`;
  downloadDataUrl(dataUrl, filename);
}

/**
 * Export the viewport to PDF
 */
export async function exportViewportToPdf(
  nodes: Node[],
  baseFilename: string = 'graph'
): Promise<void> {
  const viewport = document.querySelector('.svelte-flow__viewport');
  if (!viewport) {
    throw new Error('Viewport not found');
  }

  const bounds = calculateBounds(nodes);
  if (!bounds) {
    throw new Error('No visible nodes to export');
  }

  const viewportElement = viewport as HTMLElement;

  // html-to-image options that properly handle SVG elements (edges)
  const dataUrl = await toPng(viewportElement, {
    backgroundColor: '#ffffff',
    width: bounds.width,
    height: bounds.height,
    pixelRatio: 2,
    cacheBust: true,
    style: {
      width: `${bounds.width}px`,
      height: `${bounds.height}px`,
      transform: `translate(${-bounds.minX}px, ${-bounds.minY}px)`,
    }
  });

  // Create PDF
  const pdf = new jsPDF({
    orientation: bounds.width > bounds.height ? 'landscape' : 'portrait',
    unit: 'px',
    format: [bounds.width, bounds.height]
  });

  pdf.addImage(dataUrl, 'PNG', 0, 0, bounds.width, bounds.height);
  const filename = `${baseFilename}-${new Date().toISOString().split('T')[0]}.pdf`;
  pdf.save(filename);
}

/**
 * Helper to download a data URL as a file
 */
function downloadDataUrl(dataUrl: string, filename: string): void {
  const a = document.createElement('a');
  a.setAttribute('download', filename);
  a.setAttribute('href', dataUrl);
  a.click();
}
