import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OpsDashboard } from "@/components/OpsDashboard";

const id = "123e4567-e89b-12d3-a456-426614174000";
const record = (status: "failed" | "processing" | "completed" | "pending") => ({
  id,
  status,
  error: status === "failed" ? "Worker unavailable" : null,
  queued_at: "2026-08-23T10:00:00Z",
  created_at: "2026-08-23T10:00:00Z",
  updated_at: "2026-08-23T10:00:00Z",
  manual_retry_count: status === "pending" ? 1 : 0,
  last_manual_retry_at: status === "pending" ? "2026-08-23T10:05:00Z" : null,
  stale: false,
});

afterEach(() => vi.unstubAllGlobals());

describe("OpsDashboard", () => {
  it("renders Retry for a failed job", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ results: [record("failed")] }), { status: 200 }),
    ));
    render(<OpsDashboard />);
    expect(await screen.findByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it.each(["completed", "processing"] as const)(
    "does not render Retry for a %s job",
    async (status) => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ results: [record(status)] }), { status: 200 }),
      ));
      render(<OpsDashboard />);
      await screen.findByText(status);
      expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
    },
  );

  it("refreshes the operational list after a successful retry", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ results: [record("failed")] })))
      .mockResolvedValueOnce(new Response(JSON.stringify(record("pending")), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ results: [record("pending")] })));
    vi.stubGlobal("fetch", fetchMock);
    render(<OpsDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));
    await screen.findByText("Job successfully resubmitted to the queue.");
    expect(await screen.findByText("pending")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("surfaces an upstream conflict", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ results: [record("failed")] })))
      .mockResolvedValueOnce(new Response(
        JSON.stringify({ error: "Only failed care-plan jobs can be retried" }),
        { status: 409 },
      )));
    render(<OpsDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Only failed care-plan jobs can be retried")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled());
  });

  it("rejects malformed upstream operational payloads", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ results: [{ id, status: "failed" }] })),
    ));
    render(<OpsDashboard />);
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });
});
