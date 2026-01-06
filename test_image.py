from image_generator import generate_news_image

path = generate_news_image(
    headline="Breaking News: Major Policy Change Impacts Millions Across India Today",
    description="The government has announced a major policy reform that will directly affect citizens across multiple sectors including education, employment, and healthcare.",
    image_url="https://images.unsplash.com/photo-1504711434969-e33886168f5c",
    output_name="test_post.png"
)

print("Image saved at:", path)
