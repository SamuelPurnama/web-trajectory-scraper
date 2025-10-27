(async function() {
    console.log("[EXPAND SCRIPT] Starting expansion script.");
    const expandableSelectors = [
        '[aria-expanded="false"]',
    ];

    try {
        const elementsToClick = document.querySelectorAll(expandableSelectors.join(','));
        if (elementsToClick.length > 0) {
            console.log(`[EXPAND SCRIPT] Found ${elementsToClick.length} expandable elements to click.`);
        }

        for (const el of elementsToClick) {
            if (el && typeof el.click === 'function') {
                el.click();
                // Brief pause to allow UI to update.
                await new Promise(resolve => setTimeout(resolve, 50));
            }
        }
    } catch (error) {
        console.error("[EXPAND SCRIPT] Error during expansion:", error);
    }
})(); 