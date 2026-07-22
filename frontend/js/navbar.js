/**
 * 全局导航栏组件 — 所有页面共用
 * 用法：每个页面删除 <nav> HTML，在 <body> 开头放 <div id="navbar"></div>
 * 然后引入此脚本，再调用 Navbar.init()
 */
var Navbar = (function() {
  'use strict';

  // 所有页面的导航链接定义
  var NAV_LINKS = [
    { href: '/',              label: '首页' },
    { href: '/visualization', label: '知识星图' },
    { href: '/analysis',      label: '数据洞察' },
    { href: '/planner',       label: '学分计算' },
    { href: '/quiz',          label: '答题闯关' },
    { href: '/library',       label: '藏书阁' },
    { href: '/leaderboard',   label: '排行榜' },
  ];

  function getActivePath() {
    var p = window.location.pathname;
    if (p === '/' || p === '/index.html') return '/';
    // 匹配 /course/xxx 时高亮首页
    return p;
  }

  // ============ 渲染导航栏 ============
  function render() {
    var container = document.getElementById('navbar');
    if (!container) return;

    var activePath = getActivePath();

    // 生成导航链接 HTML（自动高亮当前页）
    var linksHtml = NAV_LINKS.map(function(link) {
      var isActive = '';
      if (link.href === '/') {
        isActive = (activePath === '/' || activePath === '') ? ' active' : '';
      } else {
        isActive = activePath.startsWith(link.href) ? ' active' : '';
      }
      return '<a href="' + link.href + '" class="' + isActive.trim() + '">' + link.label + '</a>';
    }).join('');

    // 搜索框仅首页显示
    var searchHtml = (activePath === '/' || activePath === '')
      ? '<div class="nav-search"><input type="text" id="gs" placeholder="搜索课程..." onkeydown="if(event.key===\'Enter\')Navbar.doSearch()" oninput="if(window.filterCourses)window.filterCourses()"><button class="nav-search-btn" onclick="Navbar.doSearch()" title="搜索">&#x1F50D;</button></div>'
      : '';

    var html =
      '<nav id="mainNavbar">' +
        '<div class="nav-left">' +
          '<a href="/" class="logo"><span class="dot"></span>NJU 课程星图</a>' +
          searchHtml +
        '</div>' +
        '<div class="nav-group">' +
          '<div class="nav-links">' + linksHtml + '</div>' +
          '<div class="nav-right">' +
            '<button class="theme-btn" id="themeBtn" onclick="Navbar.toggleTheme()">&#x1F319;</button>' +
            '<div style="position:relative">' +
              '<div class="user-avatar" id="ua" onclick="Navbar.toggleUserMenu()">&#x1F464;</div>' +
              '<div class="user-dropdown" id="ud">' +
                '<a href="/profile">个人主页</a>' +
                '<a href="#" onclick="Navbar.logout();return false">退出登录</a>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</nav>';

    container.innerHTML = html;
    applyTheme();
    checkAuth();
  }

  // ============ 主题 ============
  function applyTheme() {
    var dark = localStorage.getItem('theme') === 'dark';
    document.body.classList.toggle('dark', dark);
    var btn = document.getElementById('themeBtn');
    if (btn) btn.innerHTML = dark ? '&#x2600;&#xFE0F;' : '&#x1F319;';
  }

  function toggleTheme() {
    var dark = !document.body.classList.contains('dark');
    document.body.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
    var btn = document.getElementById('themeBtn');
    if (btn) btn.innerHTML = dark ? '&#x2600;&#xFE0F;' : '&#x1F319;';
    // 通知页面（如果页面有自己的主题处理函数）
    if (typeof window.onThemeChange === 'function') window.onThemeChange(dark);
  }

  // ============ 用户 ============
  function checkAuth() {
    fetch('/api/auth/status')
      .then(function(r) { return r.json(); })
      .then(function(d) {
        var avatar = document.getElementById('ua');
        if (!avatar) return;
        if (d.authenticated && d.user) {
          var name = d.user.display_name || d.user.username || '?';
          avatar.textContent = name[0] || '?';
          avatar.title = name;
        }
      })
      .catch(function() {});
  }

  function toggleUserMenu() {
    var ud = document.getElementById('ud');
    if (ud) ud.classList.toggle('show');
  }

  // 记录浏览路径（用于返回按钮）
  function trackVisit() {
    var history = JSON.parse(sessionStorage.getItem('pageHistory') || '[]');
    if (history.length === 0 || history[history.length - 1] !== location.href) {
      history.push(location.href);
      if (history.length > 10) history.shift();
      sessionStorage.setItem('pageHistory', JSON.stringify(history));
    }
  }

  function goBack() {
    var history = JSON.parse(sessionStorage.getItem('pageHistory') || '[]');
    if (history.length >= 2) {
      history.pop(); // remove current page
      var prev = history.pop(); // get previous
      sessionStorage.setItem('pageHistory', JSON.stringify(history));
      location.href = prev;
    } else if (document.referrer) {
      location.href = document.referrer;
    } else {
      location.href = '/';
    }
  }

  function doSearch() {
    if (typeof window.filterCourses === 'function') window.filterCourses();
    var el = document.getElementById('courses');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function logout() {
    fetch('/api/auth/logout', { method: 'POST' })
      .then(function() { window.location.href = '/'; })
      .catch(function() { window.location.href = '/'; });
  }

  // ============ 注入统一导航栏 CSS ============
  var NAV_CSS =
    '#mainNavbar{position:fixed!important;top:0!important;left:0!important;right:0!important;z-index:100!important;' +
    'height:60px!important;padding:0 24px!important;' +
    'display:flex!important;align-items:center!important;justify-content:space-between!important;' +
    'background:rgba(255,255,255,.92)!important;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);' +
    'border-bottom:1px solid rgba(0,0,0,.06)!important;flex-shrink:0!important}' +
    '#mainNavbar .nav-left{display:flex!important;align-items:center!important;gap:16px!important;' +
    'margin:0!important;padding:0!important;flex-shrink:0!important}' +
    '#mainNavbar .logo{font-size:17px!important;font-weight:700!important;color:inherit!important;text-decoration:none!important;' +
    'display:flex!important;align-items:center!important;gap:8px!important;font-family:inherit!important;' +
    'margin:0!important;padding:0!important;flex-shrink:0!important}' +
    '#mainNavbar .logo .dot{width:10px!important;height:10px!important;border-radius:50%!important;background:#3b82f6!important;display:inline-block!important;margin:0!important}' +
    '#mainNavbar .nav-group{display:flex!important;align-items:center!important;gap:12px!important;' +
    'margin:0!important;margin-left:auto!important;flex-shrink:0!important}' +
    '#mainNavbar .nav-links{display:flex!important;align-items:center!important;gap:2px!important;' +
    'margin:0!important;margin-left:0!important;margin-right:0!important;flex-shrink:0!important}' +
    '#mainNavbar .nav-links a{color:#64748b!important;text-decoration:none!important;font-size:13px!important;font-weight:500!important;padding:6px 14px!important;border-radius:100px!important;transition:.2s!important}' +
    '#mainNavbar .nav-links a:hover{color:#3b82f6!important;background:rgba(59,130,246,.06)!important}' +
    '#mainNavbar .nav-links a.active{color:#3b82f6!important;background:rgba(59,130,246,.1)!important}' +
    '#mainNavbar .nav-right{display:flex!important;align-items:center!important;gap:8px!important;' +
    'margin:0!important;margin-left:0!important;flex-shrink:0!important}' +
    '#mainNavbar .nav-search{display:flex!important;align-items:center!important;gap:0!important;margin:0!important}' +
    '#mainNavbar .nav-search input{width:160px!important;padding:7px 12px!important;background:rgba(0,0,0,.03)!important;border:1px solid rgba(0,0,0,.08)!important;border-radius:100px 0 0 100px!important;color:inherit!important;font-size:12px!important;outline:none!important;font-family:inherit!important;height:30px!important;box-sizing:border-box!important}' +
    '#mainNavbar .nav-search input:focus{border-color:#3b82f6!important}' +
    '#mainNavbar .nav-search-btn{display:flex!important;align-items:center!important;justify-content:center!important;width:30px!important;height:30px!important;background:rgba(0,0,0,.03)!important;border:1px solid rgba(0,0,0,.08)!important;border-left:none!important;border-radius:0 100px 100px 0!important;color:#94a3b8!important;cursor:pointer!important;font-size:13px!important;padding:0!important;flex-shrink:0!important;box-sizing:border-box!important}' +
    '#mainNavbar .nav-search-btn:hover{color:#3b82f6!important;background:rgba(59,130,246,.08)!important}' +
    '#mainNavbar .theme-btn{width:30px!important;height:30px!important;border-radius:50%!important;border:1px solid rgba(0,0,0,.1)!important;background:transparent!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:15px!important;color:#64748b!important;padding:0!important;margin:0!important;flex-shrink:0!important}' +
    '#mainNavbar .theme-btn:hover{border-color:#3b82f6!important;color:#3b82f6!important}' +
    '#mainNavbar .user-avatar{width:30px!important;height:30px!important;border-radius:50%!important;background:linear-gradient(135deg,#3b82f6,#8b5cf6)!important;display:flex!important;align-items:center!important;justify-content:center!important;color:#fff!important;font-size:13px!important;font-weight:700!important;cursor:pointer!important;margin:0!important;flex-shrink:0!important}' +
    '#mainNavbar .user-dropdown{display:none!important;position:absolute!important;top:42px!important;right:0!important;width:160px!important;background:#fff!important;border:1px solid rgba(0,0,0,.08)!important;border-radius:12px!important;box-shadow:0 8px 30px rgba(0,0,0,.1)!important;padding:4px!important;z-index:200!important}' +
    '#mainNavbar .user-dropdown.show{display:block!important}' +
    '#mainNavbar .user-dropdown a{display:block!important;padding:9px 12px!important;color:#1e293b!important;text-decoration:none!important;font-size:13px!important;border-radius:8px!important}' +
    '#mainNavbar .user-dropdown a:hover{background:rgba(0,0,0,.04)!important}' +
    // 暗色模式
    'body.dark #mainNavbar{background:rgba(15,17,22,.95)!important;border-color:rgba(255,255,255,.06)!important}' +
    'body.dark #mainNavbar .logo{color:#e2e8f0!important}' +
    'body.dark #mainNavbar .logo .dot{background:#3b82f6!important}' +
    'body.dark #mainNavbar .nav-links a{color:#94a3b8!important}' +
    'body.dark #mainNavbar .nav-links a:hover{color:#3b82f6!important;background:rgba(59,130,246,.12)!important}' +
    'body.dark #mainNavbar .nav-links a.active{color:#3b82f6!important;background:rgba(59,130,246,.15)!important}' +
    'body.dark #mainNavbar .nav-search input{background:rgba(255,255,255,.04)!important;border-color:rgba(255,255,255,.08)!important;color:#e2e8f0!important}' +
    'body.dark #mainNavbar .nav-search-btn{background:rgba(255,255,255,.04)!important;border-color:rgba(255,255,255,.08)!important;color:#94a3b8!important}' +
    'body.dark #mainNavbar .nav-search-btn:hover{background:rgba(59,130,246,.1)!important;color:#3b82f6!important}' +
    'body.dark #mainNavbar .theme-btn{border-color:rgba(255,255,255,.12)!important;color:#94a3b8!important}' +
    'body.dark #mainNavbar .theme-btn:hover{border-color:#3b82f6!important;color:#3b82f6!important}' +
    'body.dark #mainNavbar .user-dropdown{background:#1a1d26!important;border-color:rgba(255,255,255,.08)!important}' +
    'body.dark #mainNavbar .user-dropdown a{color:#e2e8f0!important}' +
    'body.dark #mainNavbar .user-dropdown a:hover{background:rgba(255,255,255,.05)!important}';

  function injectCSS() {
    var style = document.createElement('style');
    style.id = 'navbar-global-css';
    style.textContent = NAV_CSS;
    document.head.appendChild(style);
  }

  // ============ 初始化 ============
  function init() {
    trackVisit();
    injectCSS();
    // 首次加载时应用主题
    applyTheme();
    // 在 DOM ready 后渲染导航栏
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', render);
    } else {
      render();
    }
    // 点击空白处关闭用户菜单
    document.addEventListener('click', function(e) {
      var ud = document.getElementById('ud');
      var ua = document.getElementById('ua');
      if (ud && ua && ud.classList.contains('show') && !ua.contains(e.target)) {
        ud.classList.remove('show');
      }
    });
  }

  // 暴露 API
  return {
    init: init,
    render: render,
    toggleTheme: toggleTheme,
    applyTheme: applyTheme,
    toggleUserMenu: toggleUserMenu,
    logout: logout,
    checkAuth: checkAuth,
    doSearch: doSearch,
    goBack: goBack
  };
})();

// 自动初始化
Navbar.init();
