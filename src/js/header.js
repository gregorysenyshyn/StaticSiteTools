(function() {
  // ⚡ Bolt: Cache header element to avoid repeated DOM queries
  const header = document.getElementById("header");
  let ticking = false;
  let lastOpacity = 1; // Track last applied opacity

  if (header) {
    window.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

          // ⚡ Bolt: Clamp opacity and avoid unnecessary DOM writes
          let newOpacity = 1 - scrollTop / 500;

          // Clamp to [0, 1]
          if (newOpacity < 0) newOpacity = 0;
          if (newOpacity > 1) newOpacity = 1;

          // Only write to DOM if value changed significantly (0.001 precision)
          if (Math.abs(newOpacity - lastOpacity) > 0.001) {
              header.style.opacity = newOpacity;
              lastOpacity = newOpacity;
          } else if (newOpacity === 0 && lastOpacity !== 0) {
              // Ensure we hit exactly 0
              header.style.opacity = 0;
              lastOpacity = 0;
          } else if (newOpacity === 1 && lastOpacity !== 1) {
              // Ensure we hit exactly 1
              header.style.opacity = 1;
              lastOpacity = 1;
          }

          ticking = false;
        });

        ticking = true;
      }
    });
  }
})();
