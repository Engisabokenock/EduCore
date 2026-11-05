import { ImageResponse } from "next/og";

// Social preview image (WhatsApp, Facebook, X). Rendered on the edge and cached, so there is
// no static /og-image.png to forget to upload.
export const alt = "EduCore — CBC revision resources for Kenyan learners";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const runtime = "edge";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #0ea5e9 100%)",
          color: "white",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 40, fontWeight: 700, opacity: 0.9 }}>EduCore</div>
        <div style={{ fontSize: 72, fontWeight: 800, lineHeight: 1.1, marginTop: 24 }}>
          CBC worksheets, exams and notes
        </div>
        <div style={{ fontSize: 32, marginTop: 28, opacity: 0.85 }}>
          Organised by grade, subject and topic. Free downloads every day.
        </div>
      </div>
    ),
    size
  );
}
