/**
 * PocketSmart AI - Primary JavaScript
 * UI enhancements, currency formatting, form validation, and responsiveness
 */

document.addEventListener('DOMContentLoaded', () => {
    // Format INR Currency values
    document.querySelectorAll('[data-currency]').forEach(el => {
        const val = parseFloat(el.textContent.replace(/[^0-9.-]+/g, ''));
        if (!isNaN(val)) {
            el.textContent = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(val);
        }
    });

    // Dismissible alerts
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'alert-close-btn';
        closeBtn.style.cssText = 'background:none;border:none;font-size:1.2rem;cursor:pointer;margin-left:auto;color:inherit;';
        closeBtn.onclick = () => alert.remove();
        alert.appendChild(closeBtn);
    });
});
