(function () {
    // notifications.js
    // Exposes window.showNotification(message, type='info', timeout=3500)
    // Supports stacking (maxVisible), queueing, close button and animations.

    function createNotificationsModule() {
        const maxVisible = 3;

        function ensureContainer() {
            let container = document.getElementById('global-notification');
            if (!container) {
                container = document.createElement('div');
                container.id = 'global-notification';
                container.style.pointerEvents = 'none';
                container.style.position = 'fixed';
                container.style.top = '1.5rem';
                container.style.right = '1.5rem';
                container.style.zIndex = '9999';
                document.body.appendChild(container);
            }
            if (!container._queue) container._queue = [];
            return container;
        }

        function _create(container, msg, type, timeout) {
            const colors = {
                info: 'bg-blue-500 text-white',
                success: 'bg-green-500 text-white',
                error: 'bg-red-500 text-white'
            };

            const notif = document.createElement('div');
            notif.className = `notif-item max-w-sm w-full shadow-lg rounded-lg p-3 mb-3 pointer-events-auto ` + (colors[type] || colors.info);
            notif.style.transition = 'transform 250ms ease, opacity 250ms ease';
            notif.style.transform = 'translateY(-8px)';
            notif.style.opacity = '0';
            notif.style.pointerEvents = 'auto';

            notif.innerHTML = `<div class="flex items-start"><div class="flex-1 text-sm">${msg}</div><button aria-label="关闭通知" style="margin-left:0.75rem;color:inherit;opacity:0.9;background:transparent;border:0;font-size:14px;cursor:pointer">✕</button></div>`;

            const closeBtn = notif.querySelector('button');
            const hide = () => {
                notif.style.transform = 'translateY(-8px)';
                notif.style.opacity = '0';
                clearTimeout(notif._hideTimer);
                setTimeout(() => { try { notif.remove(); } catch (e) {} ; // after remove, try dequeue
                    tryDequeue(container);
                }, 260);
            };
            closeBtn.addEventListener('click', hide);

            container.prepend(notif);
            requestAnimationFrame(() => { notif.style.transform = 'translateY(0)'; notif.style.opacity = '1'; });

            if (timeout && timeout > 0) {
                notif._hideTimer = setTimeout(hide, timeout);
            }
        }

        function tryDequeue(container) {
            const visible = container.querySelectorAll('.notif-item').length;
            if (visible < maxVisible && container._queue && container._queue.length > 0) {
                const next = container._queue.shift();
                _create(container, next.msg, next.type, next.timeout);
            }
        }

        function showNotification(message, type='info', timeout=3500) {
            try {
                const container = ensureContainer();
                const visible = container.querySelectorAll('.notif-item').length;
                if (visible >= maxVisible) {
                    container._queue.push({ msg: message, type, timeout });
                } else {
                    _create(container, message, type, timeout);
                }
            } catch (e) {
                // fallback to native alert only if DOM operations fail
                try { alert(message); } catch (e2) { /* ignore */ }
            }
        }

        return { showNotification };
    }

    const mod = createNotificationsModule();
    window.showNotification = mod.showNotification;
})();
