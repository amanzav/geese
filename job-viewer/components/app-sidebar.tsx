'use client';

import * as React from 'react';
import {
  Briefcase,
  FileText,
  Settings,
  ClipboardList,
  LayoutDashboard,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from '@/components/ui/sidebar';
import { Card } from '@/components/ui/card';
import { ScrapeDialog } from '@/components/scrape-dialog';

const menuItems = [
  {
    title: 'Dashboard',
    url: '/',
    icon: LayoutDashboard,
  },
  {
    title: 'Jobs',
    url: '/jobs',
    icon: Briefcase,
  },
  {
    title: 'Cover Letters',
    url: '/cover-letters',
    icon: FileText,
  },
  {
    title: 'Applications',
    url: '/applications',
    icon: ClipboardList,
  },
];

const actionItems = [
  {
    title: 'Quick Scrape',
    action: 'scrape' as const,
    icon: RefreshCw,
  },
  {
    title: 'Settings',
    url: '/settings',
    icon: Settings,
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const [scrapeDialogOpen, setScrapeDialogOpen] = React.useState(false);

  return (
    <>
      <Sidebar variant="inset">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Briefcase className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Geese</span>
            <span className="text-xs text-muted-foreground">WaterlooWorks Automator</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* Main Navigation */}
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => {
                const isActive = pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link href={item.url}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Actions */}
        <SidebarGroup>
          <SidebarGroupLabel>Actions</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {actionItems.map((item) => {
                const isActive = pathname === item.url;
                
                // Special handling for Quick Scrape action
                if (item.action === 'scrape') {
                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton onClick={() => setScrapeDialogOpen(true)}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                }
                
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link href={item.url!}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <Card className="mx-2 mb-2 p-3">
          <div className="text-xs text-muted-foreground">
            <p className="font-medium text-foreground mb-1">Quick Stats</p>
            <p>Jobs: 0</p>
            <p>Cover Letters: 0</p>
            <p>Applied: 0</p>
          </div>
        </Card>
      </SidebarFooter>
    </Sidebar>
    
    <ScrapeDialog open={scrapeDialogOpen} onOpenChange={setScrapeDialogOpen} />
    </>
  );
}
