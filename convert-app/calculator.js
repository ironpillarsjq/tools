// 圣经章数计算器

/**
 * 计算两个圣经位置之间的总章数（含两端）
 * @param {number} startBookIndex - 起始书卷在BIBLE_BOOKS中的索引
 * @param {number} startChapter - 起始章节（1-based）
 * @param {number} endBookIndex - 结束书卷在BIBLE_BOOKS中的索引
 * @param {number} endChapter - 结束章节（1-based）
 * @returns {{success: boolean, total?: number, error?: string}}
 */
function calculateChapters(startBookIndex, startChapter, endBookIndex, endChapter) {
    var total = 0;
    var wrap = false;

    // 检测是否需要回绕：起始位置在结束位置之后
    if (startBookIndex > endBookIndex ||
        (startBookIndex === endBookIndex && startChapter > endChapter)) {
        wrap = true;

        // 起始书卷剩余章数（从起始章到该书卷末尾）
        total += BIBLE_BOOKS[startBookIndex].chapters - startChapter + 1;

        // 从下一书卷到末卷（索引65）的全部章数
        for (var i = startBookIndex + 1; i < BIBLE_BOOKS.length; i++) {
            total += BIBLE_BOOKS[i].chapters;
        }

        // 从首卷（索引0）到结束卷之前的全部章数
        for (var j = 0; j < endBookIndex; j++) {
            total += BIBLE_BOOKS[j].chapters;
        }

        // 结束书卷已过章数（从第1章到结束章）
        total += endChapter;
    } else if (startBookIndex === endBookIndex) {
        // 同书卷非回绕：结束章 - 起始章 + 1
        total = endChapter - startChapter + 1;
    } else {
        // 跨书卷非回绕
        // 起始书卷剩余章数（从起始章到该书卷末尾）
        total += BIBLE_BOOKS[startBookIndex].chapters - startChapter + 1;

        // 中间书卷全部章数
        for (var i = startBookIndex + 1; i < endBookIndex; i++) {
            total += BIBLE_BOOKS[i].chapters;
        }

        // 结束书卷已过章数（从第1章到结束章）
        total += endChapter;
    }

    return {
        success: true,
        total: total,
        wrap: wrap
    };
}
