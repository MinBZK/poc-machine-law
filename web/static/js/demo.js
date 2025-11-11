/**
 * Demo mode JavaScript functionality
 * Handles collapsible YAML sections and interactive features
 */

/**
 * Toggle a directory collapsed/expanded in the sidebar
 */
function toggleDirectory(element) {
    const directory = element.closest('.law-directory');
    if (!directory) return;

    directory.classList.toggle('collapsed');
}

/**
 * Toggle a YAML section collapsed/expanded
 */
function toggleSection(element) {
    const section = element.closest('.yaml-section');
    if (!section) return;

    const isCollapsed = section.classList.contains('collapsed');

    if (isCollapsed) {
        section.classList.remove('collapsed');
        const icon = element.querySelector('.collapse-icon');
        if (icon) icon.textContent = '▼';
    } else {
        section.classList.add('collapsed');
        const icon = element.querySelector('.collapse-icon');
        if (icon) icon.textContent = '▶';
    }
}

/**
 * Collapse all YAML sections
 */
function collapseAll() {
    document.querySelectorAll('.yaml-section').forEach(section => {
        section.classList.add('collapsed');
        const icon = section.querySelector('.collapse-icon');
        if (icon) icon.textContent = '▶';
    });
}

/**
 * Expand all YAML sections
 */
function expandAll() {
    document.querySelectorAll('.yaml-section').forEach(section => {
        section.classList.remove('collapsed');
        const icon = section.querySelector('.collapse-icon');
        if (icon) icon.textContent = '▼';
    });
}

/**
 * Initialize demo page on load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set initial collapse icons based on section state
    document.querySelectorAll('.yaml-section').forEach(section => {
        const icon = section.querySelector('.collapse-icon');
        if (!icon) return;

        if (section.classList.contains('collapsed')) {
            icon.textContent = '▶';
        } else {
            icon.textContent = '▼';
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + [ : Collapse all
        if ((e.ctrlKey || e.metaKey) && e.key === '[') {
            e.preventDefault();
            collapseAll();
        }

        // Ctrl/Cmd + ] : Expand all
        if ((e.ctrlKey || e.metaKey) && e.key === ']') {
            e.preventDefault();
            expandAll();
        }
    });
});
