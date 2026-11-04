import type { MetadataRoute } from "next";
import { serverApi } from "@/lib/server-api";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://educore.co.ke";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const urls: MetadataRoute.Sitemap = [
    { url: SITE, lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
    { url: `${SITE}/grades`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE}/pricing`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE}/search`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.6 },
  ];

  try {
    const grades = await serverApi.getGrades();
    if (grades) {
      for (const grade of grades) {
        urls.push({
          url: `${SITE}/grades/${grade.slug}`,
          lastModified: new Date(),
          changeFrequency: "weekly",
          priority: 0.8,
        });

        const subjects = (await serverApi.getSubjects(grade.slug)) ?? [];
        if (subjects) {
          for (const subject of subjects) {
            urls.push({
              url: `${SITE}/grades/${grade.slug}/${subject.slug}`,
              lastModified: new Date(),
              changeFrequency: "weekly",
              priority: 0.7,
            });

            const topics = await serverApi.getTopics(subject.slug, grade.slug);
            if (topics) {
              for (const topic of topics) {
                urls.push({
                  url: `${SITE}/grades/${grade.slug}/${subject.slug}/${topic.slug}`,
                  lastModified: new Date(),
                  changeFrequency: "daily",
                  priority: 0.6,
                });
              }
            }
          }
        }
      }
    }

    // Resources — paginate through all published resources
    let page = 1;
    while (true) {
      const data = await serverApi.getResources({ page: String(page), page_size: "100" });
      if (!data || !data.results || data.results.length === 0) break;
      for (const resource of data.results) {
        urls.push({
          url: `${SITE}/resources/${resource.slug}`,
          lastModified: new Date(resource.published_at ?? resource.created_at),
          changeFrequency: "monthly",
          priority: 0.5,
        });
      }
      if (!data.next) break;
      page++;
      if (page > 50) break; // Safety cap at 5000 URLs
    }
  } catch {
    // Partial sitemap is better than no sitemap
  }

  return urls;
}
