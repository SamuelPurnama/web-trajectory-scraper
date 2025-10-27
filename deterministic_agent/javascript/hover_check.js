(() => {
    // Only force CSS visibility of hidden elements, don't trigger events that create duplicates
    document.head.insertAdjacentHTML('beforeend', `<style>
      [hidden], [aria-hidden="true"], nav ul, .dropdown, .submenu, .flyout, .menu {
        display:block!important;visibility:visible!important;opacity:1!important;
        max-height:none!important;transform:none!important;height:auto!important;
      }
    </style>`);
    
    // Force visibility on elements that might be hidden with inline styles
    const show = e => {
      if (!e) return;
      e.style.display = 'block';
      e.style.visibility = 'visible';
      e.style.opacity = '1';
      e.style.maxHeight = 'none';
      e.style.height = 'auto';
      e.style.transform = 'none';
    };
    
    document.querySelectorAll('.dropdown,.submenu,.menu,.flyout,nav ul,nav li ul').forEach(show);
    
    // Remove duplicate links with the same URL
    const seenUrls = new Set();
    const linksToRemove = [];
    
    document.querySelectorAll('a[href]').forEach(link => {
      const url = link.href;
      if (seenUrls.has(url)) {
        // This is a duplicate - mark for removal
        linksToRemove.push(link);
      } else {
        seenUrls.add(url);
      }
    });
    
    // Remove the duplicate links
    linksToRemove.forEach(link => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
    });
  })();
