import cv2


def draw_label(frame, bbox, label, color=(0, 255, 0)):
    """
    Draw a bounding box + label (name or 'Unknown').
    
    bbox: (x1, y1, x2, y2)
    label: string to display
    color: (B, G, R)
    """

    x1, y1, x2, y2 = map(int, bbox)

    # Draw bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Calculate text size
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

    # Draw background rectangle for text
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1), color, -1)

    # Draw label text
    cv2.putText(
        frame, label,
        (x1 + 3, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (0, 0, 0), 2
    )

    return frame