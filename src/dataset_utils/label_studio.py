from dataset_utils.yolo import load_annotation


def prediction_from_yolo_annotation(
    annotation_path: str,
    index_cls_name_map: dict[int, str],
    from_name_value: str = "detec_label",
    to_name_value: str = "image",
    type_value: str = "rectanglelabels",
    source_value: str = "$image",
    model_version: str = "",
):
    annotation = load_annotation(
        annotation_path,
        format="tlwh",
        index_cls_name_map=index_cls_name_map,
    )
    return {
        "model_version": model_version,
        "result": [
            {
                "from_name": from_name_value,
                "to_name": to_name_value,
                "type": type_value,
                "source": source_value,
                "value": {
                    "rectanglelabels": str(label),
                    "x": bbox[0] * 100.0,
                    "y": bbox[1] * 100.0,
                    "width": bbox[2] * 100.0,
                    "height": bbox[3] * 100.0,
                }
            }
            for label, bbox in zip(annotation["labels"], annotation["bboxes"])
        ]
    }
