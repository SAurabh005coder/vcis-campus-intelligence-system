import { Link, Outlet } from "react-router-dom";

function AppLayout() {
  return (
    <div>
      <header>
        <h1>VCIS</h1>

        <nav>
          <Link to="/">Home</Link>{" "}
          <Link to="/students">Students</Link>
        </nav>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default AppLayout;