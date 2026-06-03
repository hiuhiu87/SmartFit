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
