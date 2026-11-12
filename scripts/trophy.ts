// Draws ryo-ma/github-profile-trophy cards locally (no hosted server, no rate limit).
// Usage: GITHUB_TOKEN1=... deno run -A scripts/trophy.ts <trophy-repo-dir> <user> <out.svg> <theme>
const [dir, user, out, themeName] = Deno.args;
const src = new URL(`file://${await Deno.realPath(dir)}/src/`);
const { GithubApiService } = await import(new URL("Services/GithubApiService.ts", src).href);
const { Card } = await import(new URL("card.ts", src).href);
const { COLORS } = await import(new URL("theme.ts", src).href);

const info = await new GithubApiService().requestUserInfo(user);
if (info?.totalCommits === undefined) throw new Error(`GitHub fetch failed: ${JSON.stringify(info)}`);
// hide "?" (unranked) trophies, one row, same panel size as the hosted service
const svg = new Card([], ["-?"], -1, 1, 115, 10, 10, false, false).render(info, COLORS[themeName]);
await Deno.writeTextFile(out, svg);
