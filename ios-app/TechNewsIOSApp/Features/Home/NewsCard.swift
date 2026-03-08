import SwiftUI

struct NewsCard: View {
    let article: Article
    let favoriteAction: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(article.displayTitle)
                        .font(.headline)
                        .fontWeight(.bold)
                        .foregroundStyle(.primary)
                        .multilineTextAlignment(.leading)

                    Text(article.displayPreview)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }

                Spacer(minLength: 8)

                Button(action: favoriteAction) {
                    Image(systemName: article.isFavorite ? "heart.fill" : "heart")
                        .font(.title3)
                        .foregroundStyle(article.isFavorite ? .red : .secondary)
                        .padding(8)
                        .background(.thinMaterial, in: Circle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(article.isFavorite ? "Remove favorite" : "Add favorite")
            }

            HStack {
                Text(article.sourceName ?? "Unknown source")
                Spacer()
                Text(DateFormatting.itemTimestamp(article.processedAt))
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Color(.secondarySystemBackground))
        )
    }
}
