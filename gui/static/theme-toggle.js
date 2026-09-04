// theme-toggle.js — Chuyển đổi giao diện Sáng / Tối (Chàm Đêm) cho TrafficVision AI
// Cách dùng: thêm 1 dòng duy nhất vào cuối mỗi file HTML (trước </body>):
//   <script src="{{ url_for('static', filename='theme-toggle.js') }}"></script>
// Script tự động: đọc theme đã lưu (localStorage) -> áp dụng ngay khi tải trang,
// và tự chèn 1 nút bấm hình mặt trời/mặt trăng vào cuối sidebar để đổi theme.

(function () {
    const STORAGE_KEY = 'tv-theme';

    function applyTheme(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    // Áp dụng ngay lập tức (trước khi vẽ trang) để không bị nháy màu
    const saved = localStorage.getItem(STORAGE_KEY) || 'dark';
    applyTheme(saved);

    document.addEventListener('DOMContentLoaded', function () {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'theme-toggle-btn';
        btn.title = 'Chuyển giao diện Sáng / Tối';

        function setIcon() {
            const current = localStorage.getItem(STORAGE_KEY) || 'dark';
            btn.innerHTML = current === 'light' ? '&#9788;' : '&#9789;'; // sun / moon
        }
        setIcon();

        btn.addEventListener('click', function () {
            const current = localStorage.getItem(STORAGE_KEY) || 'dark';
            const next = current === 'light' ? 'dark' : 'light';
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
            setIcon();
        });

        // Chèn nút ngay phía trên nút đăng xuất (nếu có), hoặc cuối sidebar
        const logoutBtn = sidebar.querySelector('.sidebar-logout');
        if (logoutBtn) {
            sidebar.insertBefore(btn, logoutBtn);
        } else {
            sidebar.appendChild(btn);
        }
    });
})();