const layoutShell = window.LayoutShell;
const layoutProfile = window.LayoutProfile;
const layoutUsers = window.LayoutUsers;
const layoutVehicles = window.LayoutVehicles;

if (!layoutShell) {
  throw new Error('No se cargó layout_shell.js antes de layout.js');
}
if (!layoutProfile) {
  throw new Error('No se cargó layout_profile.js antes de layout.js');
}
if (!layoutUsers) {
  throw new Error('No se cargó layout_users.js antes de layout.js');
}
if (!layoutVehicles) {
  throw new Error('No se cargó layout_vehicles.js antes de layout.js');
}

const {
  loadComponent,
  applySidebarAdminOnlyLinks,
  applySidebarUserName,
  applyAuthenticatedHeaderState,
  hydrateAuthUserFromProfile,
  initAuth,
  initLoginModal,
  initLogout,
} = layoutShell;

const {
  initProfilePage,
  initPasswordChange,
  initProfileEdit,
  initLicencia,
} = layoutProfile;

const { initUserDirectoryPage } = layoutUsers;
const { initVehicleDashboardPage } = layoutVehicles;

document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([
    loadComponent('header-placeholder', '/components/header.html'),
    loadComponent('sidebar-placeholder', '/components/sidebar.html'),
    loadComponent('footer-placeholder', '/components/footer.html'),
    loadComponent('login-modal-placeholder', '/components/login-modal.html'),
  ]);

  initLoginModal();
  initAuth();
  initLogout();

  const current = window.location.pathname.split('/').pop() || 'index.html';

  document.querySelectorAll('[data-sidebar-link]').forEach((link) => {
    const href = (link.getAttribute('href') || '').split('/').pop();
    if (href && href !== '#' && href === current) {
      link.classList.remove('text-slate-600', 'hover:translate-x-1');
      link.classList.add('bg-white', 'dark:bg-slate-800', 'text-blue-700', 'dark:text-blue-300', 'font-semibold', 'shadow-sm');
    }
  });

  const addUserBtn = document.getElementById('sidebar-add-user-btn');
  if (addUserBtn && current === 'dashboard_user_directory.html') {
    addUserBtn.classList.remove('hidden');
  }

  applyAuthenticatedHeaderState(current);
  applySidebarUserName();
  applySidebarAdminOnlyLinks();

  if (current !== 'perfil_view.html') {
    hydrateAuthUserFromProfile(current).catch(() => {});
  }

  await initProfilePage(current);
  initPasswordChange(current);
  await initProfileEdit(current);
  initLicencia(current);
  await initUserDirectoryPage(current);
  await initVehicleDashboardPage(current);
});
