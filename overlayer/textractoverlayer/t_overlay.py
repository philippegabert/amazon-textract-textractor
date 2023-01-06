from dataclasses import dataclass
from textractcaller.t_call import Textract_Types
from typing import List
from trp.trp2 import TDocumentSchema, TDocument, TGeometry, TextractBlockTypes


@dataclass
class DocumentDimensions:

    def __init__(self, doc_width: int, doc_height: int):
        self.__doc_width = doc_width
        self.__doc_height = doc_height

    @property
    def doc_width(self):
        return self.__doc_width

    @property
    def doc_height(self):
        return self.__doc_height


@dataclass
class BoundingBox:

    def __init__(
        self,
        geometry: TGeometry,
        document_dimensions: DocumentDimensions,
        box_type: Textract_Types,
        page_number: int,
        confidence: float,
        text: str,
    ):
        if not geometry or not document_dimensions:
            raise ValueError("need geometry and document_dimensions to create BoundingBox object")
        self.__box_type = box_type
        self.__page_number = page_number
        bbox_width = geometry.bounding_box.width
        bbox_height = geometry.bounding_box.height
        bbox_left = geometry.bounding_box.left
        bbox_top = geometry.bounding_box.top
        self.__xmin: int = round(bbox_left * document_dimensions.doc_width)
        self.__ymin: int = round(bbox_top * document_dimensions.doc_height)
        self.__xmax: int = round(self.__xmin + (bbox_width * document_dimensions.doc_width))
        self.__ymax: int = round(self.__ymin + (bbox_height * document_dimensions.doc_height))
        self.__confidence: float = round(confidence, 2)
        self.__text: str = text

    def __str__(self):
        return f"bounding_box(box_type='{self.__box_type}', page_number={self.page_number}, xmin={self.__xmin}, ymin={self.__ymin}, xmax={self.__xmax}, ymax={self.__ymax})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, obj):
        return (isinstance(obj, BoundingBox) and obj.box_type == self.__box_type and obj.xmin == self.xmin
                and obj.ymin == self.ymin and obj.xmax == self.xmax and obj.ymax == self.ymax
                and self.page_number == obj.page_number)

    @property
    def xmin(self) -> int:
        return self.__xmin

    @property
    def ymin(self) -> int:
        return self.__ymin

    @property
    def xmax(self) -> int:
        return self.__xmax

    @property
    def ymax(self) -> int:
        return self.__ymax

    @property
    def box_type(self) -> Textract_Types:
        return self.__box_type

    @property
    def page_number(self) -> int:
        return self.__page_number

    @property
    def confidence(self) -> float:
        return self.__confidence

    @property
    def text(self) -> str:
        return self.__text


def get_bounding_boxes(
    textract_document: TDocument,
    overlay_features: List[Textract_Types],
    document_dimensions: List[DocumentDimensions],
) -> List[BoundingBox]:
    bounding_box_list: List[BoundingBox] = list()
    page_number: int = 0

    for page in textract_document.pages:
        page_dimensions = document_dimensions[page_number]
        page_number += 1
        if (Textract_Types.WORD in overlay_features or Textract_Types.LINE in overlay_features):
            for line in textract_document.lines(page):
                if Textract_Types.LINE in overlay_features:
                    if line:
                        bounding_box_list.append(
                            BoundingBox(
                                geometry=line.geometry,
                                document_dimensions=page_dimensions,
                                box_type=Textract_Types.LINE,
                                page_number=page_number,
                                confidence=line.confidence,
                                text=line.text,
                            ))
                if Textract_Types.WORD in overlay_features:
                    words_of_line = textract_document.filter_blocks_by_type(textract_document.get_child_relations(line),[TextractBlockTypes.WORD])
                    for word in words_of_line:
                        if word:
                            bounding_box_list.append(
                                BoundingBox(
                                    geometry=word.geometry,
                                    document_dimensions=page_dimensions,
                                    box_type=Textract_Types.WORD,
                                    page_number=page_number,
                                    confidence=word.confidence,
                                    text=word.text,
                                ))

        if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.KEY, Textract_Types.VALUE]]):
            #for field in page.form.fields:
            for field_key in textract_document.keys(page):
                if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.KEY]]):
                    bounding_box_list.append(
                        BoundingBox(
                            geometry=field_key.geometry,
                            document_dimensions=page_dimensions,
                            box_type=Textract_Types.KEY,
                            page_number=page_number,
                            confidence=field_key.confidence,
                            text=field_key.text,
                        ))
                if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.VALUE]]):
                    field_values = textract_document.get_blocks_for_relationships(field_key.get_relationships_for_type("VALUE"))
                    for field_value in field_values:
                        bounding_box_list.append(
                            BoundingBox(
                                geometry=field_value.geometry,
                                document_dimensions=page_dimensions,
                                box_type=Textract_Types.VALUE,
                                page_number=page_number,
                                confidence=field_value.confidence,
                                text=field_value.text,
                            ))

        if any([x for x in overlay_features if x in [Textract_Types.TABLE, Textract_Types.CELL]]):
            for table in textract_document.tables(page):
                if Textract_Types.TABLE in overlay_features:
                    bounding_box_list.append(
                        BoundingBox(
                            geometry=table.geometry,
                            document_dimensions=page_dimensions,
                            box_type=Textract_Types.TABLE,
                            page_number=page_number,
                            confidence=table.confidence,
                            text="table",
                        ))
                if Textract_Types.CELL in overlay_features:
                    cells_of_table = textract_document.filter_blocks_by_type(textract_document.get_child_relations(table),[TextractBlockTypes.CELL])
                    for cell in cells_of_table:
                        bounding_box_list.append(
                                        BoundingBox(
                                            geometry=cell.geometry,
                                            document_dimensions=page_dimensions,
                                            box_type=Textract_Types.CELL,
                                            page_number=page_number,
                                            confidence=cell.confidence,
                                            text="cell",
                                        ))
        if (Textract_Types.QUERIES in overlay_features):
            for query in textract_document.queries(page):
                query_answers = textract_document.get_answers_for_query(query)
                for query_answer in query_answers:
                    bounding_box_list.append(
                                BoundingBox(
                                    geometry=query_answer.geometry,
                                    document_dimensions=page_dimensions,
                                    box_type=Textract_Types.QUERIES,
                                    page_number=page_number,
                                    confidence=query_answer.confidence,
                                    text=query_answer.text,
                                ))

    return bounding_box_list
