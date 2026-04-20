"""
Generate icon file for Clipboard Flash.
Run this once to create the .ico file.
"""

from PIL import Image, ImageDraw


def create_clipboard_icon(size):
    """Create a clipboard icon at the given size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    s = size / 64
    
    # Clipboard body (rounded rectangle)
    body_color = (124, 58, 237)  # Purple #7c3aed
    border_color = (109, 40, 217)  # Darker purple
    
    # Main clipboard body
    draw.rounded_rectangle(
        [int(8*s), int(14*s), int(56*s), int(60*s)],
        radius=int(4*s),
        fill=body_color,
        outline=border_color,
        width=max(1, int(1.5*s))
    )
    
    # Clipboard clip at top
    clip_color = (139, 92, 246)  # Lighter purple #8b5cf6
    draw.rounded_rectangle(
        [int(20*s), int(4*s), int(44*s), int(18*s)],
        radius=int(3*s),
        fill=clip_color
    )
    
    # Inner clip hole
    draw.rounded_rectangle(
        [int(26*s), int(8*s), int(38*s), int(14*s)],
        radius=int(2*s),
        fill=body_color
    )
    
    # Text lines (white)
    line_color = (255, 255, 255)
    line_width = max(1, int(2.5*s))
    
    # Line 1
    draw.line(
        [int(16*s), int(28*s), int(48*s), int(28*s)],
        fill=line_color,
        width=line_width
    )
    
    # Line 2
    draw.line(
        [int(16*s), int(38*s), int(42*s), int(38*s)],
        fill=line_color,
        width=line_width
    )
    
    # Line 3
    draw.line(
        [int(16*s), int(48*s), int(36*s), int(48*s)],
        fill=line_color,
        width=line_width
    )
    
    return img


def main():
    # Create icons at multiple sizes for .ico file
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_clipboard_icon(size) for size in sizes]
    
    # Save as .ico with all sizes
    images[0].save(
        'icon.ico',
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    
    print("Created icon.ico")
    
    # Also save a PNG for other uses
    images[-1].save('icon.png', format='PNG')
    print("Created icon.png")


if __name__ == "__main__":
    main()
