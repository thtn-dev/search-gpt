// @flow fsf
import * as React from "react";
interface Props extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}
export function ThreadRoot({ children }: Props) {
  return <div>{children}</div>;
}
