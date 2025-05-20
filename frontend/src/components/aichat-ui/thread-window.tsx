// @flow
import * as React from "react";
export interface Props extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}
export function ThreadWindow({ children, ...props }: Props) {
  return <div className={props.className}>{children}</div>;
}
