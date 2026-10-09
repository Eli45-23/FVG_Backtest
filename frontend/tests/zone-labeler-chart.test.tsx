import {test,expect} from 'vitest';
import {annotationX} from '../src/TradeInspector';
test('four-hour confirmation projects one bar after last start; five-minute default unchanged',()=>{
 const c=[{time:0},{time:14400}];
 expect(annotationX(new Date(28800*1000).toISOString(),c,n=>n*10,14400)).toBe(20);
 expect(annotationX(new Date(14700*1000).toISOString(),c,n=>n*10)).toBe(20);
});
