import axios from "axios";

export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong."
): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const status = error.response?.status;

  switch (status) {
    case 400:
      return "Invalid request.";

    case 401:
      return "You are not authenticated.";

    case 403:
      return "You are not authorized to perform this action.";

    case 404:
      return "The requested resource was not found.";

    case 409:
      return "This operation conflicts with existing data.";

    case 422:
      return "The submitted data is invalid.";

    case 500:
      return "The server encountered an error.";

    default:
      return fallback;
  }
}