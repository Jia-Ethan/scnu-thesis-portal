import { useEffect, useState } from "react";
import type { HealthResponse } from "../generated/contracts";
import { ApiError, getHealth } from "./api";

export function useWorkspaceBoot() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [bootError, setBootError] = useState<ApiError | null>(null);

  useEffect(() => {
    getHealth()
      .then((response) => {
        setHealth(response);
        setBootError(null);
      })
      .catch((err) => setBootError(err instanceof ApiError ? err : new ApiError("健康检查失败", "NETWORK_ERROR")));
  }, []);

  return { health, bootError };
}
