import MarkdownView from "./MarkdownView";

/** 简版:把 review.md 当 markdown 渲染(含闪卡表格)。P3 可改成可翻面交互卡。 */
export default function Flashcards({ reviewMd }: { reviewMd: string }) {
  if (!reviewMd.trim()) return null;
  return <MarkdownView>{reviewMd}</MarkdownView>;
}
