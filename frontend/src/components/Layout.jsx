import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import "./Layout.css";

export default function Layout({ children }) {
  return (
    <div className="layout">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Section */}
      <div className="main">
        <Topbar />

        <main className="content">
          {children}
        </main>
      </div>

    </div>
  );
}