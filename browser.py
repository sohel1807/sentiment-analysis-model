import logging
import asyncio
from datetime import datetime
from typing import Dict

from fastapi import HTTPException
from playwright.async_api import async_playwright
from modal import App, Image, web_endpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post_scraper")

# Build the container image and install Playwright dependencies.
playwright_image = (
    Image.debian_slim()
    .pip_install("playwright")
    .run_commands("playwright install-deps", "playwright install")
)

app = App(name="Headless", image=playwright_image)

@app.function(keep_warm=0)
@web_endpoint(label="scrape-facebook-post", method="POST")
async def get_facebook_post(credentials: Dict):
    post_url = credentials.get("post_url")
    if not post_url:
        logger.error("Missing required field: post_url")
        return {"error": "Missing required field: post_url"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        async def handle_dialog(dialog):
            logger.info(f"Dismissing dialog: {dialog.message}")
            await dialog.dismiss()
        page.on("dialog", handle_dialog)

        try:
            logger.info(f"Navigating directly to post URL: {post_url}")
            await page.goto(post_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            await asyncio.sleep(2)

            if "login" in page.url:
                logger.warning("Redirected to login page, navigating back")
                await page.goBack()
                await page.wait_for_load_state("networkidle", timeout=60000)
                await asyncio.sleep(2)

            await page.wait_for_selector('div[data-ad-rendering-role="story_message"]', timeout=60000)
            await asyncio.sleep(2)

            logger.info("Extracting post content and image alt text")
            post_data = await page.evaluate('''() => {
                let postContent = "";
                let postImageAlt = "";
                const postElement = document.querySelector('div[data-ad-rendering-role="story_message"]');
                if (postElement) {
                    postContent = postElement.innerText.trim();
                    const container = postElement.parentElement;
                    if (container) {
                        const images = container.querySelectorAll("img[alt]");
                        if (images.length > 0) {
                            const validAlts = Array.from(images)
                                .map(img => img.alt)
                                .filter(alt => alt && alt.length > 10);
                            postImageAlt = validAlts.join(", ");
                        }
                    }
                }
                return {
                    post_content: postContent,
                    post_url: window.location.href,
                    post_image_alt: postImageAlt
                };
            }''')
            logger.info(f"Post content extracted (first 50 chars): {post_data['post_content'][:50]}...")
            logger.info(f"Post image alt text: {post_data['post_image_alt']}")

            # Scrape comments by scrolling within the specified container.
            comments = []
            total_count = 0
            max_comments = 50

            while total_count < max_comments:
                logger.info("Scrolling the designated comments container to trigger dynamic loading")
                await page.evaluate('''() => {
                    // Target the inner container from your snippet:
                    const container = document.querySelector('div.html-div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x78zum5.xdt5ytf.x1iyjqo2.x7ywyr2');
                    if (container) {
                        container.scrollTop = container.scrollHeight;
                    }
                }''')
                await asyncio.sleep(2)

                logger.info("Extracting comments from rendered HTML")
                new_comments = await page.evaluate('''() => {
                    const comments = [];
                    const containers = document.querySelectorAll('div[role="article"]');
                    containers.forEach(container => {
                        if (container.closest('div[data-ad-rendering-role="story_message"]')) return;
                        const textElement = container.querySelector('div[dir="auto"][style*="text-align: start"]');
                        if (textElement) {
                            const commentText = textElement.innerText.trim();
                            if (commentText) {
                                comments.push({ 'comment': commentText });
                            }
                        }
                    });
                    return comments;
                }''')
                logger.info(f"Found {len(new_comments)} new comments")
                existing_comments = set(c["comment"] for c in comments)
                filtered_new_comments = [c for c in new_comments if c["comment"] not in existing_comments]
                logger.info(f"Filtered to {len(filtered_new_comments)} unique new comments")
                total_count += len(filtered_new_comments)
                comments.extend(filtered_new_comments)

                if len(filtered_new_comments) == 0:
                    logger.info("No more new comments loaded; breaking out of loop")
                    break

            logger.info(f"Total comments collected: {len(comments)}")
            formatted_data = {
                "post": {
                    "content": post_data["post_content"],
                    "url": post_data["post_url"],
                    "image_alt": post_data["post_image_alt"],
                },
                "comments": comments[:max_comments],
                "metadata": {
                    "total_comments": total_count,
                    "scraped_at": datetime.now().isoformat(),
                    "comment_limit_reached": len(comments) >= max_comments,
                },
            }

            logger.info("Scraping complete, closing browser")
            await browser.close()
            return formatted_data

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            await browser.close()
            raise HTTPException(status_code=500, detail=f"Error scraping post: {str(e)}")
