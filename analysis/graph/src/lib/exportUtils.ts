import { toPng } from 'html-to-image';

export interface Node {
  id?: string;
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
  // Capture the entire flow container to include edges (SVG layer) and nodes
  const flowElement = document.querySelector('.svelte-flow');
  if (!flowElement) {
    throw new Error('Flow container not found');
  }

  const bounds = calculateBounds(nodes);
  if (!bounds) {
    throw new Error('No visible nodes to export');
  }

  const flow = flowElement as HTMLElement;

  // Force inline styles on SVG elements before capture
  const svgElements = flow.querySelectorAll('svg, path, line, polyline, circle, ellipse, rect');
  svgElements.forEach((el) => {
    const computed = window.getComputedStyle(el);
    const htmlEl = el as HTMLElement;
    htmlEl.style.stroke = computed.stroke;
    htmlEl.style.strokeWidth = computed.strokeWidth;
    htmlEl.style.fill = computed.fill;
    htmlEl.style.opacity = computed.opacity;
  });

  // Capture with filter to exclude UI controls
  const dataUrl = await toPng(flow, {
    backgroundColor: '#ffffff',
    pixelRatio: 6, // Very high resolution for crisp exports
    cacheBust: true,
    skipFonts: false,
    filter: (node) => {
      // Exclude controls, minimap, and background from export
      if (node.classList) {
        return !node.classList.contains('svelte-flow__controls') &&
               !node.classList.contains('svelte-flow__minimap') &&
               !node.classList.contains('svelte-flow__background');
      }
      return true;
    }
  });

  const filename = `${baseFilename}-${new Date().toISOString().split('T')[0]}.png`;
  downloadDataUrl(dataUrl, filename);
}

/**
 * Export the viewport to SVG - Direct extraction approach
 */
export async function exportViewportToSvg(
  nodes: Node[],
  baseFilename: string = 'graph'
): Promise<void> {
  const flowElement = document.querySelector('.svelte-flow');
  if (!flowElement) {
    throw new Error('Flow container not found');
  }

  const bounds = calculateBounds(nodes);
  if (!bounds) {
    throw new Error('No visible nodes to export');
  }

  // Find the SVG element that contains the edges
  const edgesSvg = flowElement.querySelector('.svelte-flow__edges');

  // Create a new SVG document
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('xmlns', svgNS);
  svg.setAttribute('width', bounds.width.toString());
  svg.setAttribute('height', bounds.height.toString());
  svg.setAttribute('viewBox', `${bounds.minX} ${bounds.minY} ${bounds.width} ${bounds.height}`);

  // Add white background
  const background = document.createElementNS(svgNS, 'rect');
  background.setAttribute('x', bounds.minX.toString());
  background.setAttribute('y', bounds.minY.toString());
  background.setAttribute('width', bounds.width.toString());
  background.setAttribute('height', bounds.height.toString());
  background.setAttribute('fill', '#ffffff');
  svg.appendChild(background);

  // Clone and add edges (paths from the edges SVG)
  if (edgesSvg) {
    const paths = edgesSvg.querySelectorAll('path, line, polyline');
    paths.forEach((path) => {
      const clonedPath = path.cloneNode(true) as SVGElement;
      const computed = window.getComputedStyle(path);
      clonedPath.setAttribute('stroke', computed.stroke);
      clonedPath.setAttribute('stroke-width', computed.strokeWidth);
      clonedPath.setAttribute('fill', computed.fill);
      clonedPath.setAttribute('opacity', computed.opacity);
      if (computed.markerEnd) clonedPath.setAttribute('marker-end', computed.markerEnd);
      if (computed.markerStart) clonedPath.setAttribute('marker-start', computed.markerStart);
      svg.appendChild(clonedPath);
    });

    // Clone marker definitions (for arrowheads)
    const defs = edgesSvg.querySelector('defs');
    if (defs) {
      svg.appendChild(defs.cloneNode(true));
    }
  }

  // Add nodes as rectangles with text
  const visibleNodes = nodes.filter(n => !n.hidden);
  for (const node of visibleNodes) {
    const x = node.position.x;
    const y = node.position.y;
    const width = node.width || 280;
    const height = node.height || 100;

    // Get the actual node element to extract text and styles
    const nodeElement = document.querySelector(`[data-id="${node.id}"]`);
    const nodeRect = document.createElementNS(svgNS, 'rect');
    nodeRect.setAttribute('x', x.toString());
    nodeRect.setAttribute('y', y.toString());
    nodeRect.setAttribute('width', width.toString());
    nodeRect.setAttribute('height', height.toString());
    nodeRect.setAttribute('rx', '8');

    if (nodeElement) {
      const computed = window.getComputedStyle(nodeElement);
      nodeRect.setAttribute('fill', computed.backgroundColor || '#ffffff');
      nodeRect.setAttribute('stroke', computed.borderColor || '#e5e7eb');
      nodeRect.setAttribute('stroke-width', '2');
    } else {
      nodeRect.setAttribute('fill', '#ffffff');
      nodeRect.setAttribute('stroke', '#e5e7eb');
      nodeRect.setAttribute('stroke-width', '2');
    }
    svg.appendChild(nodeRect);

    // Add text from node
    if (nodeElement) {
      const textContent = nodeElement.textContent?.trim() || '';
      const text = document.createElementNS(svgNS, 'text');
      text.setAttribute('x', (x + width / 2).toString());
      text.setAttribute('y', (y + height / 2).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dominant-baseline', 'middle');
      text.setAttribute('font-size', '14');
      text.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
      text.setAttribute('fill', '#111827');
      text.textContent = textContent;
      svg.appendChild(text);
    }
  }

  // Serialize SVG to string
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svg);

  // Create data URL
  const dataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString);

  const filename = `${baseFilename}-${new Date().toISOString().split('T')[0]}.svg`;
  downloadDataUrl(dataUrl, filename);
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
