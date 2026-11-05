/**
 * Route segment layout for /admin. The admin shell (sidebar, header, role gate) is
 * rendered by each page through <AdminLayout title=...> so every page sets its own
 * title; this file only passes children through, so the shell is not rendered twice.
 */
export default function AdminSegmentLayout({ children }: { children: React.ReactNode }) {
  return children;
}
