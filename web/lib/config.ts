const internalApiBaseUrl =
  process.env.INTERNAL_API_BASE_URL ?? "http://lan-control-plane-server:8000";

function getBrowserWsUrl(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/client`;
}

export const config = {
  apiBaseUrl: "/api",
  internalApiBaseUrl,
  getWsClientUrl(): string {
    return getBrowserWsUrl();
  },
};
