"""
MkDocs hook: Normalize blog post previews for consistent listing display.

PURPOSE
-------
This hook ensures every blog post on /blog/ renders a consistent "media object"
preview card: thumbnail + title + meta + short excerpt + "Read more →".

RULES APPLIED (only to blog posts under blog/posts/):
1. LEAD IMAGE: If no markdown image appears before the first H2, prepend a
   fallback image so the listing always has a thumbnail.
2. EXCERPT BREAK: Automatically insert `<!-- more -->` after the Description
   section (or first content paragraph if no Description), so excerpts are
   consistently short. Any existing `<!-- more -->` is removed first to
   ensure correct placement.

WHY THIS APPROACH?
- Authors don't need to manually add `<!-- more -->` - the hook handles it.
- Posts without a hero image still get a visually consistent listing.
- The Description section (## Description) becomes the canonical excerpt source.
- Full post pages are unaffected - changes only impact the listing/excerpt.

CONTENT STRUCTURE EXPECTED:
    ---
    frontmatter
    ---
    ![Hero Image](path/to/image.png)   <- optional, fallback added if missing
    # Title
    
    ## Description
    One or two sentence summary of the post.   <- this becomes the excerpt
    
    ## Rest of content...

If ## Description is absent, the first paragraph after the title becomes the excerpt.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page
    from mkdocs.config.defaults import MkDocsConfig

# Fallback image used when no lead image exists in the post.
# Path is relative to the post location (blog/posts/) -> ../../assets/
FALLBACK_IMAGE = "![FIT Orb](../../assets/orb.png)"

# Front-matter keys that indicate an image is defined in metadata
IMAGE_META_KEYS = frozenset({
    "image", "cover", "banner", "thumbnail", "hero",
    "featured_image", "featured-image", "og_image",
})

# Regex patterns
RE_IMAGE = re.compile(r"^\s*!\[.*?\]\(.*?\)")
RE_HEADING = re.compile(r"^\s*#+\s+")
RE_H1 = re.compile(r"^\s*#\s+[^#]")
RE_H2 = re.compile(r"^\s*##\s+[^#]")
RE_DESCRIPTION_H2 = re.compile(r"^\s*##\s+description\s*$", re.IGNORECASE)
RE_EXCERPT_MARKER = re.compile(r"<!--\s*more\s*-->", re.IGNORECASE)
RE_BLANK = re.compile(r"^\s*$")
RE_HR = re.compile(r"^\s*[-*_]{3,}\s*$")


def _is_blank(line: str) -> bool:
    """Check if line is empty or whitespace only."""
    return bool(RE_BLANK.match(line))


def _is_image(line: str) -> bool:
    """Check if line starts with a markdown image."""
    return bool(RE_IMAGE.match(line))


def _is_heading(line: str) -> bool:
    """Check if line is any markdown heading."""
    return bool(RE_HEADING.match(line))


def _is_h1(line: str) -> bool:
    """Check if line is an H1 heading."""
    return bool(RE_H1.match(line))


def _is_h2(line: str) -> bool:
    """Check if line is an H2 heading."""
    return bool(RE_H2.match(line))


def _is_description_h2(line: str) -> bool:
    """Check if line is specifically '## Description'."""
    return bool(RE_DESCRIPTION_H2.match(line))


def _is_hr(line: str) -> bool:
    """Check if line is a horizontal rule."""
    return bool(RE_HR.match(line))


def _is_structural(line: str) -> bool:
    """Check if line is structural (heading, image, HR, blank, or HTML comment)."""
    stripped = line.strip()
    return (
        _is_blank(line) or
        _is_heading(line) or
        _is_image(line) or
        _is_hr(line) or
        stripped.startswith("<!--") or
        stripped.startswith(">")  # blockquote
    )


def _find_first_content_line(lines: list[str], start: int = 0) -> int | None:
    """Find first line that is actual content (not blank, heading, image, etc.)."""
    for i in range(start, len(lines)):
        if not _is_structural(lines[i]) and lines[i].strip():
            return i
    return None


def _find_paragraph_end(lines: list[str], start: int) -> int:
    """
    Find the end of a paragraph starting at `start`.
    A paragraph ends at a blank line, heading, or end of file.
    """
    i = start
    while i < len(lines):
        if _is_blank(lines[i]) or _is_heading(lines[i]) or _is_hr(lines[i]):
            return i
        i += 1
    return i


def _find_h1_index(lines: list[str]) -> int | None:
    """Find the index of the first H1 heading."""
    for i, line in enumerate(lines):
        if _is_h1(line):
            return i
    return None


def _find_description_h2_index(lines: list[str]) -> int | None:
    """Find the index of '## Description' heading."""
    for i, line in enumerate(lines):
        if _is_description_h2(line):
            return i
    return None


def _has_lead_image(lines: list[str]) -> bool:
    """
    Check if there's a lead image before the first H2.
    The lead image should appear somewhere before any H2 section starts.
    """
    for line in lines:
        if _is_image(line):
            return True
        if _is_h2(line):
            # Reached an H2 without finding an image
            return False
    return False


def _remove_excerpt_markers(markdown: str) -> str:
    """Remove all existing <!-- more --> markers from the content."""
    return RE_EXCERPT_MARKER.sub("", markdown)


def _insert_excerpt_marker(lines: list[str], position: int) -> list[str]:
    """Insert <!-- more --> at the specified position."""
    # Ensure we don't insert in the middle of content
    lines.insert(position, "\n<!-- more -->\n")
    return lines


def on_page_markdown(
    markdown: str,
    page: "Page",
    config: "MkDocsConfig",
    files: "Files",
) -> str:
    """
    MkDocs hook to normalize blog post content for consistent listing display.
    
    Only processes pages under blog/posts/.
    """
    # Only process blog posts
    src_path = getattr(page.file, "src_path", "")
    if not src_path.replace("\\", "/").startswith("blog/posts/"):
        return markdown
    
    # Get page metadata
    meta = getattr(page, "meta", {}) or {}
    
    # Step 1: Remove any existing excerpt markers to ensure clean placement
    markdown = _remove_excerpt_markers(markdown)
    
    # Convert to lines for processing
    lines = markdown.split("\n")
    
    # Step 2: Check if we need to add a fallback lead image
    # Skip if front-matter defines an image
    has_meta_image = any(key in meta for key in IMAGE_META_KEYS)
    
    if not has_meta_image and not _has_lead_image(lines):
        # Find where to insert the fallback image (before the H1 title)
        h1_idx = _find_h1_index(lines)
        if h1_idx is not None:
            # Insert fallback image before the H1
            lines.insert(h1_idx, FALLBACK_IMAGE)
            lines.insert(h1_idx + 1, "")  # Add blank line after image
        else:
            # No H1 found, prepend at the beginning
            lines.insert(0, FALLBACK_IMAGE)
            lines.insert(1, "")
    
    # Step 3: Determine where to place the excerpt marker
    desc_idx = _find_description_h2_index(lines)
    
    if desc_idx is not None:
        # Found ## Description - insert excerpt after the first paragraph under it
        # Skip blank lines after the heading
        i = desc_idx + 1
        while i < len(lines) and _is_blank(lines[i]):
            i += 1
        
        # Skip any image directly under Description
        if i < len(lines) and _is_image(lines[i]):
            i += 1
            while i < len(lines) and _is_blank(lines[i]):
                i += 1
        
        # Find the first content paragraph
        content_start = _find_first_content_line(lines, i)
        if content_start is not None:
            # Find end of this paragraph
            para_end = _find_paragraph_end(lines, content_start)
            lines = _insert_excerpt_marker(lines, para_end)
    else:
        # No ## Description section - insert after first paragraph following the H1
        h1_idx = _find_h1_index(lines)
        search_start = (h1_idx + 1) if h1_idx is not None else 0
        
        # Skip blanks and any image right after H1
        i = search_start
        while i < len(lines) and _is_blank(lines[i]):
            i += 1
        
        # Skip image if present
        if i < len(lines) and _is_image(lines[i]):
            i += 1
            while i < len(lines) and _is_blank(lines[i]):
                i += 1
        
        # Find first content paragraph
        content_start = _find_first_content_line(lines, i)
        if content_start is not None:
            para_end = _find_paragraph_end(lines, content_start)
            lines = _insert_excerpt_marker(lines, para_end)
    
    return "\n".join(lines)
