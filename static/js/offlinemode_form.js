document.addEventListener('DOMContentLoaded', function () {
  // Fix for undefined in form URLs
  const form = document.getElementById('offlinemode_form');
  if (form) {
    // Ensure form doesn't have action URL ending with "undefined"
    form.addEventListener('submit', function (e) {
      const formAction = form.getAttribute('action');
      if (formAction && formAction.endsWith('undefined')) {
        // Remove the undefined part
        form.setAttribute('action', formAction.replace('/undefined', ''));
      }
    });
  }
});
