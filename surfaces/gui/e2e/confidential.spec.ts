import { expect } from "@playwright/test";
import { test } from "./fixtures";

test("confidential mode is explicit, fixed to TrustedRouter, and never remembered", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByTestId("new-confidential-session").click();

  const banner = page.getByTestId("confidential-banner");
  await expect(banner).toBeVisible();
  await expect(banner).toContainText("FastWorker will not save this conversation");
  await expect(banner).toContainText("Files you create and actions you take outside the chat can remain");
  await expect(page.getByTitle("Confidential session", { exact: true })).toBeVisible();
  await expect(page.getByTestId("session-subtitle")).toHaveText(
    "History off · TrustedRouter Confidential",
  );
  await expect(
    page.getByRole("heading", { name: "What should we work on privately?" }),
  ).toBeVisible();
  await expect(page.getByText("Chat history stays off.", { exact: false })).toBeVisible();

  const model = page.getByTestId("confidential-model");
  await expect(model).toHaveText("TrustedRouter Confidential");
  await expect(model).toHaveAttribute("title", "Fixed route: trustedrouter/confidential");

  const remembered = await page.evaluate(() =>
    localStorage.getItem("coworker:last-session-by-agent:v1"),
  );
  expect(remembered || "").not.toContain("__confidential__");

  const composer = page.getByPlaceholder(/Ask confidentially/);
  await composer.fill("keep this private");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(
    page.getByText(
      "Echo: keep this private [model=trustedrouter:trustedrouter/confidential]",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(banner).toBeVisible();

  await banner.getByRole("button", { name: "End session" }).click();
  await expect(banner).toHaveCount(0);
  await expect(page.getByTestId("confidential-model")).toHaveCount(0);
  await expect(page.getByTitle("New session", { exact: true })).toBeVisible();
});

test("collapsed navigation keeps confidential mode one click away", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Meta+b");

  const cluster = page.getByTestId("topbar-cluster");
  await cluster.getByRole("button", { name: "New confidential session" }).click();

  await expect(page.getByTestId("confidential-banner")).toBeVisible();
  await expect(cluster.getByRole("button", { name: "New confidential session" })).toHaveClass(
    /confidential-active/,
  );
});
