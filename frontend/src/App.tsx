import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';

/**
 * 这是我们React应用的根组件。
 * 它的核心职责是决定当前应该向用户显示哪个页面。
 */
function App() {
  // 我们通过检查 localStorage 中是否存在 'authToken' 来判断用户是否已登录。
  // localStorage 是浏览器提供的一种本地存储方式，关闭浏览器后数据依然存在。
  const isLoggedIn = !!localStorage.getItem('authToken');

  // 这里是核心的条件渲染逻辑：
  // 如果 isLoggedIn 为 true，我们就渲染主界面 (DashboardPage)。
  // 如果 isLoggedIn 为 false，我们就渲染认证页面 (AuthPage)。
  return isLoggedIn ? <DashboardPage /> : <AuthPage />;
}

export default App;

