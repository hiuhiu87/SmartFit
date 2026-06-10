import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case decodingError
    case unauthorized
    case server(code: String, message: String)
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The request URL is invalid."
        case .invalidResponse:
            return "The server returned an invalid response."
        case .decodingError:
            return "Unable to process server data."
        case .unauthorized:
            return "Your session has expired. Please sign in again."
        case let .server(_, message):
            return message
        case let .transport(error):
            return error.localizedDescription
        }
    }
}

extension Error {
    var isCancellation: Bool {
        if self is CancellationError {
            return true
        }

        if let apiError = self as? APIError,
           case let .transport(underlyingError) = apiError {
            return underlyingError.isCancellation
        }

        if let urlError = self as? URLError {
            return urlError.code == .cancelled
        }

        let nsError = self as NSError
        return nsError.domain == NSURLErrorDomain && nsError.code == NSURLErrorCancelled
    }
}
