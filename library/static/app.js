// Small enhancements. Every page still works without this file, except the payment pop-up.
(function () {
  var confirmDialog = document.getElementById('confirm-dialog');
  var pendingForm = null;

  // Ask before running any form marked with data-confirm (deleting a book or a member).
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!confirmDialog || typeof confirmDialog.showModal !== 'function') return;
    if (!form.hasAttribute || !form.hasAttribute('data-confirm')) return;
    event.preventDefault();
    pendingForm = form;
    confirmDialog.querySelector('[data-confirm-message]').textContent = form.getAttribute('data-confirm');
    confirmDialog.querySelector('[data-confirm-accept]').textContent = form.getAttribute('data-confirm-label') || 'Delete';
    confirmDialog.showModal();
  });

  if (confirmDialog) {
    confirmDialog.querySelector('[data-confirm-accept]').addEventListener('click', function () {
      confirmDialog.close();
      if (pendingForm) {
        pendingForm.removeAttribute('data-confirm');
        pendingForm.submit();
      }
    });
  }

  // Record a payment: fill the pop-up with the member's details.
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-pay-action]');
    var dialog = document.getElementById('pay-dialog');
    if (!button || !dialog) return;
    var due = button.getAttribute('data-pay-due');
    var amount = dialog.querySelector('input[name="amount"]');
    dialog.querySelector('form').action = button.getAttribute('data-pay-action');
    dialog.querySelector('[data-pay-summary]').textContent =
      button.getAttribute('data-pay-name') + ' owes ' + button.getAttribute('data-pay-due-text') + '.';
    amount.max = due;
    amount.value = due;
    dialog.showModal();
    amount.select();
  });

  // Close buttons and clicks on the dim backdrop.
  document.addEventListener('click', function (event) {
    var closer = event.target.closest('[data-close]');
    if (closer) {
      closer.closest('dialog').close();
      return;
    }
    if (event.target.tagName === 'DIALOG') {
      event.target.close();
    }
  });

  // Dismiss flash messages.
  document.addEventListener('click', function (event) {
    var button = event.target.closest('.flash-close');
    if (button) button.closest('.flash').remove();
  });
})();
