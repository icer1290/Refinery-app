import MarkdownUI
import SwiftUI

extension Theme {
    static let techNewsDeepSearch = Theme.gitHub
        .text {
            FontSize(.em(0.97))
            ForegroundColor(.primary)
            BackgroundColor(nil)
        }
        .strong {
            FontWeight(.semibold)
        }
        .link {
            ForegroundColor(.blue)
        }
        .paragraph { configuration in
            configuration.label
                .relativeLineSpacing(.em(0.18))
                .markdownMargin(top: 0, bottom: 14)
        }
        .blockquote { configuration in
            configuration.label
                .padding(.vertical, 10)
                .padding(.leading, 18)
                .padding(.trailing, 14)
                .background(Color(.tertiarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3, style: .continuous)
                        .fill(Color.accentColor.opacity(0.55))
                        .frame(width: 4)
                        .padding(.vertical, 10)
                        .padding(.leading, 8)
                }
                .markdownMargin(top: 6, bottom: 16)
        }
        .table { configuration in
            ScrollView(.horizontal, showsIndicators: false) {
                configuration.label
            }
            .markdownMargin(top: 6, bottom: 16)
        }
        .thematicBreak {
            Divider()
                .overlay(Color(.separator))
                .markdownMargin(top: 4, bottom: 18)
        }
}
